import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Base URL of the website to scrape
base_url = 'https://www.amazon.in/s?k=laptop&page='

# Headers to mimic a real browser request
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.6478.115 Safari/537.36'
}

# Setup session with retry logic
session = requests.Session()
retry = Retry(
    total=5,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["HEAD", "GET", "OPTIONS"]
)
adapter = HTTPAdapter(max_retries=retry)
session.mount("https://", adapter)
session.mount("http://", adapter)

# Function to scrape a single page
def scrape_page(url):
    try:
        response = session.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f'Error retrieving the webpage: {e}')
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    products = []

    product_containers = soup.find_all('div', class_='s-result-item')
    for container in product_containers:
        try:
            name = container.find('span', class_='a-size-medium').text.strip() if container.find('span', class_='a-size-medium') else 'N/A'
            price = container.find('span', class_='a-price-whole').text.strip() if container.find('span', class_='a-price-whole') else 'N/A'
            rating = container.find('span', class_='a-icon-alt').text.strip().split()[0] if container.find('span', class_='a-icon-alt') else 'N/A'
            availability = container.find('span', class_='a-declarative').text.strip() if container.find('span', class_='a-declarative') else 'N/A'
            product_url = 'https://www.amazon.in' + container.find('a', class_='a-link-normal')['href'] if container.find('a', class_='a-link-normal') else 'N/A'
            products.append({
                'Name': name,
                'Price': price,
                'Rating': rating,
                'Availability': availability,
                'Product URL': product_url
            })
        except AttributeError as e:
            logging.error(f'Error parsing product: {e}')
    
    return products

# Function to handle pagination
def scrape_all_pages(start_page=1, end_page=3):
    all_products = []
    for page in range(start_page, end_page + 1):
        logging.info(f'Scraping page {page}')
        url = base_url + str(page)
        products = scrape_page(url)
        all_products.extend(products)
        # Implementing a delay to avoid being blocked
        time.sleep(2)
    return all_products

# Scrape all pages and save the data to a CSV file
all_products = scrape_all_pages(start_page=1, end_page=3)  # Adjust end_page as needed
df = pd.DataFrame(all_products)
df.to_csv('detailed_amazon_products.csv', index=False)
logging.info('Scraping completed and data saved to detailed_amazon_products.csv')
