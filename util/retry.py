import functools
import json
import time

def retry_until_valid_json(max_retries=3, delay=1):
    """
    A decorator to retry a function if its return value is not a valid JSON string.

    :param max_retries: Maximum number of retries.
    :param delay: Delay between retries in seconds.
    :return: The decorator function.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                result = func(*args, **kwargs)
                
                cleaned_result = result.strip()
                if cleaned_result.startswith("```json"):
                    cleaned_result = cleaned_result[7:]
                elif cleaned_result.startswith("```"):
                    cleaned_result = cleaned_result[3:]

                if cleaned_result.endswith("```"):
                    cleaned_result = cleaned_result[:-3]
                
                cleaned_result = cleaned_result.strip()

                try:
                    json.loads(cleaned_result)
                    return cleaned_result  # It's valid JSON, return it
                except json.JSONDecodeError:
                    print(result)
                    print(f"Attempt {attempt + 1} of {max_retries} failed: not a valid JSON. Retrying in {delay}s...")
                    if attempt == max_retries - 1:
                        raise ValueError(f"Failed to get valid JSON after {max_retries} attempts.")
                    time.sleep(delay)
        return wrapper
    return decorator
