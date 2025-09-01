import requests
from bs4 import BeautifulSoup
import json
import logging
import os
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def clean_text(text):
    """Replaces unusual line terminators and other weird whitespace."""
    if not isinstance(text, str):
        return text
    # Replace line separator and paragraph separator characters with a standard newline
    text = text.replace('\u2028', '\n').replace('\u2029', '\n')
    # Replace non-breaking spaces with a regular space
    text = text.replace('\xa0', ' ')
    # Remove any other non-printable characters
    return re.sub(r'[^\x20-\x7E\n\r\t]', '', text)

def get_details(url):
    """Fetches and parses the details page for an art call."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        description_div = soup.find('div', class_='single_job_listing')
        
        if description_div:
            text = description_div.get_text(separator='\\n', strip=True)
            return clean_text(text)
        else:
            logging.warning(f"Could not find description on page: {url}")
            return "Description not found."
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching detail page {url}: {e}")
        return "Could not fetch details."

def scrape_art_calls():
    """
    Scrapes art call details from the California Arts Council website and saves them to a JSON file.
    """
    processed_data_filename = 'processed_data/CA_arts_council_processed_data.json'
    existing_urls = set()

    if os.path.exists(processed_data_filename):
        with open(processed_data_filename, 'r', encoding='utf-8') as f:
            try:
                processed_data = json.load(f)
                for item in processed_data:
                    if 'url' in item:
                        existing_urls.add(item['url'])
                logging.info(f"Loaded {len(existing_urls)} existing URLs from {processed_data_filename}")
            except json.JSONDecodeError:
                logging.warning(f"Could not decode JSON from {processed_data_filename}. Starting with an empty set of URLs.")

    base_url = "https://arts.ca.gov/opportunities/?fwp_job_category_tags=artist-calls%2Cgrants"
    art_calls = []
    page = 1

    while True:
        paginated_url = f"{base_url}&fwp_paged={page}"
        logging.info(f"Fetching main opportunities page: {paginated_url}")
        try:
            response = requests.get(paginated_url)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching the main URL: {e}")
            break

        soup = BeautifulSoup(response.content, 'html.parser')
        
        listings = soup.find_all('li', class_='job_listing')
        
        if not listings:
            logging.info(f"No more listings found on page {page}. Ending scrape.")
            break

        logging.info(f"Found {len(listings)} art calls on page {page}. Scraping details...")

        for listing in listings:
            title_element = listing.find('h3')
            company_element = listing.find('div', class_='job_company')
            location_and_deadline_element = listing.find('div', class_='location')
            link_element = listing.find('a')

            if not all([title_element, link_element]):
                logging.warning("Skipping a listing due to missing title or link.")
                continue

            title = clean_text(title_element.get_text(strip=True))
            company = clean_text(company_element.get_text(strip=True)) if company_element else 'N/A'
            
            location = 'N/A'
            deadline = 'N/A'
            if location_and_deadline_element:
                location_deadline_text = clean_text(location_and_deadline_element.get_text(strip=True))
                if '|' in location_deadline_text:
                    parts = location_deadline_text.split('|', 1)
                    location = parts[0].strip()
                    deadline_text = parts[1].strip()
                    if 'Deadline:' in deadline_text:
                        deadline = deadline_text.replace('Deadline:', '').strip()
                else:
                    location = location_deadline_text

            details_url = link_element['href']

            if details_url in existing_urls:
                logging.info(f"Skipping already processed URL: {details_url}")
                continue

            logging.info(f"Scraping details for: {title}")
            description = get_details(details_url)

            art_calls.append({
                'title': title,
                'organization': company,
                'location': location,
                'deadline': deadline,
                'url': details_url,
                'description': description
            })
        
        page += 1
    
    output_filename = 'raw_data/CA_arts_council_raw_data.json'
    os.makedirs(os.path.dirname(output_filename), exist_ok=True)
    
    logging.info(f"Saving {len(art_calls)} art calls to {output_filename}")
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(art_calls, f, indent=4, ensure_ascii=False)
    
    logging.info("Scraping finished successfully.")

if __name__ == "__main__":
    scrape_art_calls()
