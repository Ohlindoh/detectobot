import os
import argparse
import openai
import time
from detectobot.agents.feed_watcher import get_latest_article_links
import requests
from bs4 import BeautifulSoup
from readability import Document

# Initialize OpenAI client
openai.api_key = os.environ.get("OPENAI_API_KEY")
assistant = openai.beta.assistants.create(
    name="Threat Intel Summarizer",
    instructions="You are a threat-intel summarization assistant. Summarize the following article in ~200 words and list any MITRE ATT&CK technique IDs you find.",
    model="gpt-4o"
)


def summarise_text(text):
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Threat intel summarizer")
    parser.add_argument('--dry-run', action='store_true', help='Preview without API call')
    args = parser.parse_args()

    for feed in get_latest_article_links():
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
            summary = summarise_text(article_text)
            print("[SUMMARY]")
            print(summary)