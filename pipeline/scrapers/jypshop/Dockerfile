# JYP Shop Albums Scraper
# Extends the base image with scraper code

FROM kpop-scraper-base:test

WORKDIR /app

# Copy common utilities
COPY pipeline/common /app/pipeline/common

# Copy scraper
COPY pipeline/scrapers/jypshop/scraper.py /app/scraper.py

# Run scraper
# Use ENTRYPOINT so we can pass arguments (--vendor, --start-date, etc.)
ENTRYPOINT ["python", "scraper.py"]
CMD ["--vendor", "jypshop"]

