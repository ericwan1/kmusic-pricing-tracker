# Building the Base Docker Image

## Quick Start

```bash
cd pipeline/base
docker build -t kpop-scraper-base:latest .
```

## For Google Cloud

```bash
# Set your GCP project
export PROJECT_ID=your-project-id

# Build and push to Google Container Registry
docker build -t gcr.io/${PROJECT_ID}/kpop-scraper-base:latest .
docker push gcr.io/${PROJECT_ID}/kpop-scraper-base:latest

# Or use Artifact Registry (recommended)
docker build -t us-central1-docker.pkg.dev/${PROJECT_ID}/kpop-scrapers/base:latest .
docker push us-central1-docker.pkg.dev/${PROJECT_ID}/kpop-scrapers/base:latest
```

## Testing the Image

```bash
# Test Chrome installation
docker run --rm kpop-scraper-base:latest google-chrome --version

# Test ChromeDriver (if pre-installed, otherwise webdriver-manager handles it)
docker run --rm kpop-scraper-base:latest chromedriver --version || echo "ChromeDriver will be installed by webdriver-manager at runtime"

# Test Python environment
docker run --rm kpop-scraper-base:latest python -c "import selenium; print('Selenium:', selenium.__version__)"
```

## Image Size Optimization

The base image is ~1.5GB due to Chrome. To reduce size:
- Use multi-stage builds for scraper-specific images
- Consider using `python:3.10-slim` variants
- Remove build dependencies after installation

## Notes

- ChromeDriver version matching: The image attempts to pre-install ChromeDriver, but `webdriver-manager` (included in requirements) will automatically download the correct version at runtime if needed.
- The image runs as non-root user (`scraper`) for security.
- Cloud Run will handle user permissions automatically.

