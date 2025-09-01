import json
import os
from util.openai_caller import get_openai_response_in_json
from tqdm import tqdm

def load_json_file(file_path):
    """Loads a JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json_file(data, file_path):
    """Saves data to a JSON file."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def main():
    # Define file paths
    raw_data_path = 'raw_data/CA_arts_council_raw_data.json'
    prompts_path = 'prompts/prompts.json'
    processed_data_path = 'processed_data/CA_arts_council_processed_data.json'

    # Load data and prompts
    events = load_json_file(raw_data_path)
    prompts = load_json_file(prompts_path)
    summarize_prompt_template = prompts['summarize_description']

    processed_events = []

    # Process each event
    for event in tqdm(events, desc="Summarizing events"):
        description = event.get('description')
        if not description:
            processed_events.append(event)
            continue

        prompt = f"{summarize_prompt_template}\n\n{description}"

        try:
            summary_json_str = get_openai_response_in_json(prompt)
            summary_data = json.loads(summary_json_str)
            event.update(summary_data)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON for event: {event.get('title')}. Error: {e}")
            print(f"Failed to process. Raw response: {summary_json_str}")
        except Exception as e:
            print(f"An unexpected error occurred for event: {event.get('title')}. Error: {e}")
        
        processed_events.append(event)

    # Save the processed data
    save_json_file(processed_events, processed_data_path)
    print(f"\nSuccessfully processed {len(processed_events)} events.")
    print(f"Processed data saved to {processed_data_path}")

if __name__ == '__main__':
    main()
