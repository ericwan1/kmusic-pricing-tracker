# kmusic-pricing-tracker
There are dozens of sites on the internet that sell K-Pop merchandise. Some are the official sites for entertainment companies; others are sites run by private businesses and individuals. The goal of this project is to identify which sites offer the best deals on K-Pop merchandise. The goal is to include all products, from albums to stickers, light sticks, toys, and more. 

### Choosing Sites to Scrape
The sites currently chosen for scraping were selected because of their popularity within the collector circuit (Kpopalbums.com, Musicplaza.com, etc.). Some of these online stores also have a physical presence as well (choicemusicla.com). In version 1, official sites were selected as well (thejypshop.com). While there does not exist an estimation of total amount of money spent on these stores as a quantity or percentage of the total amount of money spent per year, the frequency of these sites in blogs, forums, and comments sections indicate that these sites are among the most popular places where Americans spend money on K-Pop merchandise. 

### Workflow
Scraping is orchestrated and done through Google Cloud. Using Google Cloud Scheduler, a Pub/Sub topic is made for the specific script that we want to have executed. The subscriber is a function in Google Cloud Functions, which executes the script it contains and writes the data to BigQuery. Currently, scraped data is stored in multiple BigQuery tables. 

Code is written and uploaded to Github periodically and the script code is copy pasted into GCP. 

### Current Headaches/To-Do
Automate some of the selenium scripts; Also will need to build a dashboard to enable others to access scraped data. 