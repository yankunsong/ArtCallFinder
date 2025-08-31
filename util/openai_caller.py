from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=api_key)

def get_openai_response(prompt: str) -> str:
    response = client.responses.create(
        model="gpt-4.1",
        input=prompt
    )
    return response.output_text

if __name__ == "__main__":
    example_prompt = "Write a one-sentence bedtime story about a unicorn."
    output = get_openai_response(example_prompt)
    print(output)