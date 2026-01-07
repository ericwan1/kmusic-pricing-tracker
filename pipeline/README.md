# K-Pop Pricing Pipeline

Batch scraper pipeline that runs weekly, scrapes K-Pop merch sites, and publishes to Kaggle.

## What's Here

```
pipeline/
├── base/              # Docker base image (Chrome + Python deps)
├── scrapers/          # Individual site scrapers
│   └── jypshop/       # JYP Shop scraper (albums + merch)
├── common/            # Shared code (storage, validation, schema)
└── deploy/            # Cloud Run / Scheduler configs (Coming soon...)
```

## Base Image

The base image has everything needed to run scrapers:
- Python 3.10
- Chrome + ChromeDriver
- All Python packages (selenium, pandas, google-cloud, etc.)

Build it:
```bash
docker build -f pipeline/base/Dockerfile -t kpop-scraper-base:test .
```

## Schema

All scrapers output the same schema:
- `item` - Product name
- `url` - Product URL
- `artist` - Artist/group name (nullable)
- `discount_price` - Discounted price (nullable)
- `price` - Current price
- `sold_out` - Boolean
- `ds` - Date partition (YYYY-MM-DD)

## Scrapers

Each scraper:
1. Extends the base image
2. Imports common utilities (storage, validation, schema)
3. Scrapes data and maps to the fixed schema
4. Uploads to GCS as JSONL (date-partitioned)
5. Exits with proper error codes

### JYP Shop Scraper

Scrapes albums and/or merchandise from JYP Shop.

```bash
# Build JYPShop Scraper
docker build -f pipeline/scrapers/jypshop/Dockerfile -t jypshop-scraper:test .

# Running the container locally (scrapes both albums and merch by default)
docker run --rm --shm-size=2g \
  -e GCS_RAW_BUCKET=your-bucket \
  -e GOOGLE_APPLICATION_CREDENTIALS=/tmp/key.json \
  -v ~/key.json:/tmp/key.json:ro \
  jypshop-scraper:test

# Or specify what to scrape
docker run ... jypshop-scraper:test --type albums
docker run ... jypshop-scraper:test --type merch
docker run ... jypshop-scraper:test --type all
```

## Common Utilities

- `schema.py` - Fixed schema definition and validation
- `storage.py` - GCS upload (date-partitioned JSONL)
- `validation.py` - Data quality checks (freshness, volume, nulls)
- `logging.py` - Structured JSON logging for Cloud Logging

## Data Flow

1. Scraper runs → outputs JSONL to GCS
2. Raw data: `gs://bucket/raw/{vendor}/ds={YYYY-MM-DD}/file.jsonl`
3. (Future) Clean/dedupe → BigQuery
4. (Future) Publish → Kaggle

## Local Testing

1. Build base image
2. Build scraper image
3. Set up GCP credentials (service account key file)
4. Set `GCS_RAW_BUCKET` env var
5. Run container

See `pipeline/scrapers/jypshop/DOCKER_RUN.md` for details.

## Cloud Deployment

Not set up yet. Plan:
- Cloud Run Jobs for each scraper
- Cloud Scheduler (weekly cron)
- Service account attached to jobs (no key files needed)

## Notes

- Raw data is append-only (idempotent by `url + ds`)
- All scrapers must validate against fixed schema
- Structured logging for debugging
- Exit codes: 0=success, 1=scraping error, 2=validation error, 3=storage error
