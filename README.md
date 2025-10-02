# ArtCallFinder

Tools for collecting art-call opportunities from state arts council websites, enriching them with AI-generated summaries, and exporting the results for review.

## Features
- Scrapers for California and Arizona arts council listings with built-in duplicate skipping (respects previously processed URLs).
- OpenAI-powered post-processing to normalize deadlines and summarize requirements/topics for each opportunity.
- Excel exporter that merges processed JSON records into a reviewable spreadsheet with hyperlinks and timestamped entries.
- Prompt templates and utility scripts to tune summarization behaviour and reconcile datasets.

## Repository Layout
- `scrapers/CA_arts_council_scraper.py` & `scrapers/AZ_arts_council_scraper.py`: state-specific web scrapers that write raw listings to `raw_data/<STATE>_raw_data.json`.
- `event_summarizer.py`: enriches raw listings via OpenAI and appends the results to `processed_data/<STATE>_processed_data.json`.
- `util/excel_writer.py`: converts processed JSON records into `art_calls.xlsx` while preserving prior rows.
- `util/openai_caller.py`: shared OpenAI helpers plus JSON-safe retry logic from `util/retry.py`.
- `prompts/prompts.json`: templates that control deadline normalization and description summarization.
- `replace.py`: optional helper to sync the `topics` column in `art_calls.xlsx` from an external `art_calls2.xlsx` file.

## Prerequisites
- Python 3.10 or newer.
- An OpenAI API key with access to the model declared in `util/openai_caller.py` (`gpt-5-mini` by default).
- Recommended packages from `requirements.txt`. If you encounter import errors for `tqdm` or `python-dotenv`, install them with `pip install tqdm python-dotenv`.

## Setup
1. (Optional) create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file at the project root (or export environment variables) containing:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## Usage
### Quick start (one command)
Run the full scrape → summarize → export pipeline in a single call:
```bash
python run_pipeline.py
```
Optional flags:
- `--max-pages <n>` limits paginated scrapers that support the argument (useful for testing).
- `--skip-scrape`, `--skip-summarize`, `--skip-export` let you rerun individual stages.
- `--verbose` enables debug logs.

### Manual steps
#### 1. Collect raw opportunity data
Run the scrapers you need; each writes a JSON file under `raw_data/`:
```bash
python scrapers/CA_arts_council_scraper.py
python scrapers/AZ_arts_council_scraper.py
```
Scrapers skip URLs already present in the corresponding `processed_data/<STATE>_processed_data.json` file so you can run them incrementally.

#### 2. Summarize and normalize listings
Enrich the newly scraped listings with AI summaries and standardized deadlines:
```bash
python event_summarizer.py
```
The script reads the prompts in `prompts/prompts.json`, calls OpenAI concurrently, and appends the structured results to `processed_data/<STATE>_processed_data.json`.

#### 3. Export to Excel for review (optional)
Convert the processed JSON files into a spreadsheet that tracks review status and preserves hyperlinks:
```bash
python util/excel_writer.py
```
The exporter only appends rows for URLs that are not yet present in `art_calls.xlsx`. Deadlines are converted to Excel date values, and each row includes the source JSON filename.

## Customizing the prompts
Adjust `prompts/prompts.json` to change how deadlines are formatted or how descriptions are summarized. Keep the response structure aligned with `event_summarizer.py` (expects `topics_EN`, `fees`, and `requirement`).

## Troubleshooting
- **API errors or rate limits**: rerun `event_summarizer.py`; failed events remain in `raw_data` until successfully processed.
- **Import errors**: ensure optional dependencies (`python-dotenv`, `tqdm`) are installed and the virtual environment is active.
- **Missing Excel columns**: the exporter expects the default header order; delete `art_calls.xlsx` to regenerate it if it gets out of sync.
