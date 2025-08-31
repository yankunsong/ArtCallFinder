import requests
from bs4 import BeautifulSoup
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
            return description_div.get_text(separator='\\n', strip=True)
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
    base_url = "https://arts.ca.gov/opportunities/?fwp_job_category_tags=artist-calls%2Cgrants"
    art_calls = []

    logging.info(f"Fetching main opportunities page: {base_url}")
    try:
        response = requests.get(base_url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching the main URL: {e}")
        return

    soup = BeautifulSoup(response.content, 'html.parser')
    
    listings = soup.find_all('li', class_='job_listing')
    
    if not listings:
        logging.warning("No job listings found. The website structure may have changed.")
        return

    logging.info(f"Found {len(listings)} art calls. Scraping details...")

    for listing in listings:
        title_element = listing.find('h3')
        company_element = listing.find('div', class_='job_company')
        location_and_deadline_element = listing.find('div', class_='location')
        link_element = listing.find('a')

        if not all([title_element, link_element]):
            logging.warning("Skipping a listing due to missing title or link.")
            continue

        title = title_element.get_text(strip=True)
        company = company_element.get_text(strip=True) if company_element else 'N/A'
        
        location = 'N/A'
        deadline = 'N/A'
        if location_and_deadline_element:
            location_deadline_text = location_and_deadline_element.get_text(strip=True)
            if '|' in location_deadline_text:
                parts = location_deadline_text.split('|', 1)
                location = parts[0].strip()
                deadline_text = parts[1].strip()
                if 'Deadline:' in deadline_text:
                    deadline = deadline_text.replace('Deadline:', '').strip()
            else:
                location = location_deadline_text

        details_url = link_element['href']

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
    
    output_filename = 'art_calls.json'
    logging.info(f"Saving {len(art_calls)} art calls to {output_filename}")
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(art_calls, f, indent=4, ensure_ascii=False)
    
    logging.info("Scraping finished successfully.")

if __name__ == "__main__":
    scrape_art_calls()
