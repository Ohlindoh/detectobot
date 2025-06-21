import os
import argparse
import openai
import time
import requests
import sys
from bs4 import BeautifulSoup
from readability import Document

# Add the parent directory to sys.path to allow absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from detectobot.watcher import get_new_site_links, load_config

# Initialize OpenAI client
openai.api_key = os.environ.get("OPENAI_API_KEY")
assistant = openai.beta.assistants.create(
    name="Threat Intel Summarizer",
    instructions="You are a threat-intel summarization assistant. Summarize the following article in ~200 words and list any MITRE ATT&CK technique IDs you find.",
    model="gpt-4o"
)


def summarize_text(text):
    """Send text to the OpenAI Assistant and return the summary."""
    thread = openai.beta.threads.create()
    openai.beta.threads.messages.create(thread_id=thread.id, role="user", content=text)
    run = openai.beta.threads.runs.create(thread_id=thread.id, assistant_id=assistant.id)
    
    # Wait for completion
    while True:
        run_status = openai.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        if run_status.status == "completed":
            break
        time.sleep(1)
    
    messages = openai.beta.threads.messages.list(thread_id=thread.id)
    for m in messages:
        if m.role == "assistant":
            return m.content[0].text.value
    
    return "[No summary returned]"

def main():
    parser = argparse.ArgumentParser(description="Threat intel summarizer")
    parser.add_argument('--dry-run', action='store_true', help='Preview without API call')
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    args = main()

    # Get articles from configured sites
    new_links = get_new_site_links()
    if not new_links:
        print("No new articles found.")
        exit(0)
    
    # Process only the first article for now
    # In the future, we'll check if it's already been summarized
    feed = new_links[0]
    if feed:
        name = feed['name']
        link = feed['link']
        print(f"\n=== Feed: {name} ===")
        print(f"Article URL: {link}")
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            response = requests.get(link, headers=headers, timeout=10)
            response.raise_for_status()
            # Try to extract main content using readability-lxml
            try:
                doc = Document(response.text)
                article_html = doc.summary()
                soup = BeautifulSoup(article_html, 'html.parser')
                article_text = soup.get_text(separator='\n')
                if not article_text.strip():
                    raise ValueError("Readability returned empty text")
            except Exception:
                # Fallback to joining all <p> tags
                soup = BeautifulSoup(response.text, 'html.parser')
                paragraphs = soup.find_all('p')
                article_text = '\n'.join(p.get_text() for p in paragraphs)
                if not article_text.strip():
                    article_text = soup.get_text()
        except Exception as e:
            print(f"[ERROR] Failed to fetch or parse article: {e}")
            article_text = ""
        if args.dry_run:
            print("[PREVIEW] Article text (first 500 chars):")
            print(article_text[:7000] + ("..." if len(article_text) > 7000 else ""))
        else:
            summary = summarize_text(article_text)
            print("[SUMMARY]")
            print(summary)