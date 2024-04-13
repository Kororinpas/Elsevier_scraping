
# Elsevier Economics Papers Scraper

## Overview
This repository contains a Python script that utilizes Playwright to scrape economic research papers published on Elsevier over the past five years. The main purpose of this scraper is to gather detailed information about these papers to facilitate academic research and analysis.

## Project Structure

- `Web_scraping.py`: Contains the main script for scraping the data using Playwright.
- `data/basic_information/`: Directory containing the initial data files which are used by the scraper to understand which papers need to be fetched.
- `data/dataset/`: Contains the results of the scraping process, with detailed information for each paper that has been successfully scraped.


## Data Description

- **Basic Information**: The `basic_information` folder contains files that list the economic papers that will be targeted by the scraper. These files are essential for the initial setup of the scraping process.

- **Dataset**: After running the script, the `dataset` folder will contain detailed information about each scraped paper, including fields like author, publication date, DOI, abstract, and more.



