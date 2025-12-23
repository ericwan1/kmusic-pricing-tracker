# kmusic-pricing-tracker
There are dozens of sites on the internet that sell K-Pop merchandise. Some are the official sites for entertainment companies; others are sites run by private businesses and individuals. The goal of this project is to identify which sites offer the best deals on K-Pop merchandise. The goal is to include all products, from albums to stickers, light sticks, toys, and more. 

### Choosing Sites to Scrape
The sites currently chosen for scraping were selected because of their popularity within the collector circuit (Kpopalbums.com, Musicplaza.com, etc.). Some of these online stores also have a physical presence as well (choicemusicla.com). In version 1, official sites were selected as well (thejypshop.com). While there does not exist an estimation of total amount of money spent on these stores as a quantity or percentage of the total amount of money spent per year, the frequency of these sites in blogs, forums, and comments sections indicate that these sites are among the most popular places where Americans spend money on K-Pop merchandise. 

### Workflow
Scraping is orchestrated through **Google Cloud Run Jobs** and **Cloud Scheduler**. The pipeline:
1. **Cloud Scheduler** triggers weekly batch jobs
2. **Cloud Run Jobs** execute containerized Selenium scrapers
3. Raw data is written to **Google Cloud Storage** (date-partitioned)
4. Data is validated, deduplicated, and loaded to **BigQuery**
5. Cleaned dataset is automatically published to **Kaggle**

See `pipeline/README.md` for detailed architecture and setup instructions.

### Current Status
- ✅ Base Docker image with Chrome + Selenium
- 🚧 Refactoring scrapers for Cloud Run
- ⏳ Setting up data validation and deduplication
- ⏳ Kaggle publishing automation 