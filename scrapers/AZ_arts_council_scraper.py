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
        
        description_div = soup.find('div', id='content')
        
        if description_div:
            text = description_div.get_text(separator='\\n', strip=True)
            return clean_text(text)
        else:
            logging.warning(f"Could not find description div with id='content' on page: {url}")
            return "Description not found."
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching detail page {url}: {e}")
        return "Could not fetch details."

def scrape_art_calls(max_pages=None):
    """
    Scrapes art call details from the Arizona Commission on the Arts website and saves them to a JSON file.
    """
    processed_data_filename = 'processed_data/AZ_arts_council_processed_data.json'
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

    base_url = "https://azarts.gov/opportunities/arts-opportunities/?sort_order=date+desc"
    art_calls = []
    page = 1

    while True:
        if max_pages and page > max_pages:
            logging.info(f"Reached max pages limit: {max_pages}. Stopping scrape.")
            break

        paginated_url = f"{base_url}&sf_paged={page}"
        logging.info(f"Fetching main opportunities page: {paginated_url}")
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
            }
            response = requests.get(paginated_url, headers=headers)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching the main URL: {e}")
            break

        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Check for "No Results Found" message to terminate scraping
        if "No Results Found" in soup.get_text():
            logging.info(f"No results found on page {page}. Ending scrape.")
            break
        
        listings_headings = soup.find_all('h3')

        if not listings_headings:
            logging.info(f"No headings found on page {page}. Ending scrape.")
            break

        logging.info(f"Found {len(listings_headings)} potential art calls on page {page}. Processing...")

        for heading in listings_headings:
            link_element = heading.find('a')

            if not link_element or not link_element.has_attr('href'):
                # This filters out headings that are not opportunity listings like "Search Arts Opportunities"
                continue
            
            title = clean_text(heading.get_text(strip=True))
            details_url = link_element['href']

            if details_url in existing_urls:
                logging.info(f"Skipping already processed URL: {details_url}")
                continue

            logging.info(f"Scraping details for: {title}")
            description = get_details(details_url)

            organization = 'N/A'
            deadline = 'N/A'

            # Extract Organization and Deadline by taking the first line of the matched text.
            org_match = re.search(r"Organization/Company:\\s*(.*)", description, re.IGNORECASE)
            if org_match:
                full_text = clean_text(org_match.group(1).strip())
                organization = full_text.split('\\n')[0].strip()
                if organization.startswith('n'):
                    organization = organization[1:]

            deadline_match = re.search(r"Deadline:\\s*(.*)", description, re.IGNORECASE)
            if deadline_match:
                full_text = clean_text(deadline_match.group(1).strip())
                deadline = full_text.split('\\n')[0].strip()
                if deadline.startswith('n'):
                    deadline = deadline[1:]

            art_calls.append({
                'title': title,
                'organization': organization,
                'location': 'N/A', # Location is not consistently provided on the listing page
                'deadline': deadline,
                'url': details_url,
                'description': description
            })
        
        page += 1
    
    output_filename = 'raw_data/AZ_arts_council_raw_data.json'
    os.makedirs(os.path.dirname(output_filename), exist_ok=True)
    
    if art_calls:
        logging.info(f"Saving {len(art_calls)} new art calls to {output_filename}")
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(art_calls, f, indent=4, ensure_ascii=False)
    else:
        logging.info("No new art calls to save.")
    
    logging.info("Scraping finished successfully.")

if __name__ == "__main__":
    scrape_art_calls(max_pages=100)