# read art_calls2.xlsx and art_calls.xlsx

# use url as the identifier. Update art_calls.xlsx. For each row, the 'topics' column should be the topics from art_calls2.xlsx.
import pandas as pd

def update_topics():
    """
    Reads art_calls.xlsx and art_calls2.xlsx, and updates the 'topics' column
    in art_calls.xlsx based on the 'url' column as an identifier.
    """
    try:
        # Read the source of truth for topics
        df_new_topics = pd.read_excel('art_calls2.xlsx')
        
        # Read the file to be updated
        df_to_update = pd.read_excel('art_calls.xlsx')

        # Create a mapping from url to topics from art_calls2.xlsx
        # This is efficient and handles missing data well.
        topic_map = df_new_topics.set_index('url')['topics']

        # Update the topics column in the main dataframe.
        # The .get(url, original_topic) approach is robust.
        # It tries to get a new topic from the map, but if the URL isn't found,
        # it keeps the original topic.
        df_to_update['topics'] = df_to_update.apply(
            lambda row: topic_map.get(row['url'], row['topics']),
            axis=1
        )

        # Save the updated dataframe back to the original file
        df_to_update.to_excel('art_calls.xlsx', index=False)

        print("Successfully updated 'topics' in art_calls.xlsx from art_calls2.xlsx.")

    except FileNotFoundError as e:
        print(f"Error: {e}. Make sure both art_calls.xlsx and art_calls2.xlsx are in the same directory.")
    except KeyError as e:
        print(f"Error: Missing column {e}. Please ensure both Excel files have 'url' and 'topics' columns.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    update_topics()