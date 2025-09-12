from openai import OpenAI
from dotenv import load_dotenv
import os
import json
from util.retry import retry_until_valid_json

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
MODEL="gpt-5-mini"

client = OpenAI(api_key=api_key)

def get_openai_response(prompt: str) -> str:
    """Gets a string response from OpenAI."""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

@retry_until_valid_json(max_retries=3)
def get_openai_response_in_json(prompt: str) -> str:
    """Gets a JSON response from OpenAI, with retries."""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful assistant that always responds with valid JSON."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

if __name__ == "__main__":
    # Example for get_openai_response
    print("--- Testing get_openai_response (string output) ---")
    example_prompt_str = "Write a one-sentence bedtime story about a unicorn."
    output_str = get_openai_response(example_prompt_str)
    print("Raw output:")
    print(output_str)
    print("-" * 20)

    # Example for get_openai_response_in_json
    print("\n--- Testing get_openai_response_in_json (JSON output) ---")
    example_prompt_json = "Return a JSON object with a single key 'story' and a one-sentence bedtime story about a unicorn as the value."
    output_json_str = get_openai_response_in_json(example_prompt_json)
    print("Raw output:")
    print(output_json_str)
    
    try:
        output_json = json.loads(output_json_str)
        print("\nParsed JSON object:")
        print(output_json)
        print(f"\nType of parsed object: {type(output_json)}")
    except json.JSONDecodeError:
        print("\nOutput was not valid JSON.")