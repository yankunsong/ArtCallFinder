import json
import os
from util.openai_caller import get_openai_response_in_json, get_openai_response
from tqdm import tqdm
import concurrent.futures

def load_json_file(file_path):
    """Loads a JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json_file(data, file_path):
    """Saves data to a JSON file."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def process_event(event, summarize_prompt_template, date_formatter_prompt_template):
    """Processes a single event to summarize description and format deadline."""
    description = event.get('description')
    if description:
        prompt = f"{summarize_prompt_template}\n\n{description}"
        try:
            summary_json_str = get_openai_response_in_json(prompt)
            summary_data = json.loads(summary_json_str)
            event.update(summary_data)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON for event: {event.get('title')}. Error: {e}")
            # Decide how to handle this error, maybe return event without summary
        except Exception as e:
            print(f"An unexpected error occurred during summary: {event.get('title')}. Error: {e}")

    # Format the deadline using OpenAI
    deadline = event.get('deadline')
    if deadline:
        try:
            date_prompt = f"{date_formatter_prompt_template}\n\n{deadline}"
            formatted_date = get_openai_response(date_prompt)
            event['deadline'] = formatted_date.strip()
        except Exception as e:
            print(f"An unexpected error occurred while formatting date for event: {event.get('title')}. Error: {e}")
    
    return event

def main():
    scraper_dir = 'scrapers'
    raw_data_dir = 'raw_data'
    processed_data_dir = 'processed_data'
    prompts_path = 'prompts/prompts.json'

    # Load prompts once
    prompts = load_json_file(prompts_path)
    summarize_prompt_template = prompts['summarize_description']
    date_formatter_prompt_template = prompts['date_formatter']

    scraper_files = [f for f in os.listdir(scraper_dir) if f.endswith('_scraper.py')]

    for scraper_file in scraper_files:
        state_prefix = scraper_file.replace('_scraper.py', '')
        print(f"--- Processing data for {state_prefix.upper()} ---")

        raw_data_path = os.path.join(raw_data_dir, f'{state_prefix}_raw_data.json')
        processed_data_path = os.path.join(processed_data_dir, f'{state_prefix}_processed_data.json')

        if not os.path.exists(raw_data_path):
            print(f"Raw data file not found for {state_prefix}, skipping.")
            continue

        # Load data
        events = load_json_file(raw_data_path)

        # Load existing processed data if it exists
        if os.path.exists(processed_data_path):
            processed_events = load_json_file(processed_data_path)
        else:
            processed_events = []
        
        # Create a set of existing URLs for quick lookup
        existing_urls = {event['url'] for event in processed_events if 'url' in event}

        # Filter out events that are already processed
        new_events = [event for event in events if event.get('url') not in existing_urls]

        if not new_events:
            print(f"No new events to process for {state_prefix.upper()}.")
            print(f"Total events for {state_prefix.upper()}: {len(processed_events)}")
            continue

        processed_new_events = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_event = {executor.submit(process_event, event, summarize_prompt_template, date_formatter_prompt_template): event for event in new_events}
            for future in tqdm(concurrent.futures.as_completed(future_to_event), total=len(new_events), desc=f"Processing new events for {state_prefix.upper()}"):
                try:
                    processed_event = future.result()
                    processed_new_events.append(processed_event)
                except Exception as exc:
                    event_title = future_to_event[future].get('title', 'Unknown Event')
                    print(f"'{event_title}' generated an exception: {exc}")

        processed_events.extend(processed_new_events)

        # Save the processed data
        save_json_file(processed_events, processed_data_path)
        print(f"\nSuccessfully processed {len(new_events)} new events for {state_prefix.upper()}.")
        print(f"Total events for {state_prefix.upper()} now: {len(processed_events)}")
        print(f"Processed data saved to {processed_data_path}\n")

if __name__ == '__main__':
    main()
