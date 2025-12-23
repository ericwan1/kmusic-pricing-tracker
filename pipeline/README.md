# K-Pop Pricing Pipeline

Production-ready batch data pipeline for scraping K-Pop merchandise pricing data.

## Architecture

- **Cloud Run Jobs**: Containerized scrapers running on a schedule
- **Cloud Scheduler**: Weekly cron triggers
- **GCS**: Raw data storage (date-partitioned)
- **BigQuery**: Cleaned, deduplicated dataset
- **Kaggle**: Public dataset publishing

## Directory Structure

```
pipeline/
├── base/              # Base Docker image with Chrome + dependencies
│   ├── Dockerfile
│   ├── requirements.txt
│   └── entrypoint.sh
├── scrapers/          # Individual scraper implementations
│   ├── smglobalshop/
│   ├── kpopalbums/
│   └── ...
├── common/            # Shared utilities
│   ├── storage.py     # GCS operations
│   ├── validation.py  # Data quality checks
│   ├── schema.py      # Fixed schema definition
│   └── logging.py     # Structured logging
└── deploy/            # Deployment configs
    ├── cloudbuild.yaml
    └── scheduler.yaml
```

## Base Image

The base Docker image (`pipeline/base/`) includes:
- Python 3.10
- Google Chrome (stable)
- ChromeDriver (matching Chrome version)
- All Python dependencies

### Building the Base Image

```bash
cd pipeline/base
docker build -t gcr.io/YOUR_PROJECT/kpop-scraper-base:latest .
docker push gcr.io/YOUR_PROJECT/kpop-scraper-base:latest
```

## Schema

Fixed schema for all scrapers:
- `item` (string): Product name
- `url` (string): Product URL
- `artist` (string): Artist/group name
- `discount_price` (float, nullable): Discounted price if available
- `price` (float): Current price
- `sold_out` (boolean): Availability status
- `ds` (date): Date partition (YYYY-MM-DD)

## Development

1. Base image provides Chrome + Python environment
2. Each scraper extends base or uses it directly
3. Scrapers write to GCS in raw format
4. Common utilities handle validation, deduplication, and publishing

