#!/usr/bin/env python3
"""
Article summarizer script for detectobot.
This script reads the YAML config and summarizes the most recent article.
"""
import os
import argparse
import time
import yaml
import requests
import sqlite3
from bs4 import BeautifulSoup
from readability import Document
import openai
from urllib.parse import urljoin

# Paths
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.yaml')
DB_PATH = os.path.join(os.path.dirname(__file__), 'watcher.db')

# Initialize OpenAI client
openai.api_key = os.environ.get("OPENAI_API_KEY")
assistant = openai.beta.assistants.create(
    name="Threat Intel Summarizer",
    instructions="You are a threat-intel summarization assistant. Summarize the following article in ~200 words and list any MITRE ATT&CK technique IDs you find.",
    model="gpt-4o"
)

def load_config():
    """Load the configuration from YAML file."""
    with open(CONFIG_PATH, 'r') as f:
        config = yaml.safe_load(f)
    return config

def init_db(conn):
    """Initialize the database if it doesn't exist."""
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS entries (
        id INTEGER PRIMARY KEY,
        hash TEXT UNIQUE,
        source TEXT,
        title TEXT,
        link TEXT,
        date TEXT,
        processed INTEGER DEFAULT 0
    )
    ''')
    conn.commit()

def entry_hash(entry):
    """Generate a hash for an entry based on its link."""
    link = entry.get('link', '')
    return str(hash(link))

def check_and_store(conn, hash_val, source, entry):
    """Check if an entry exists and store it if not."""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM entries WHERE hash = ?", (hash_val,))
    result = cursor.fetchone()
    if result:
        return False
    
    title = entry.get('title', '')
    link = entry.get('link', '')
    date = entry.get('published', '')
    
    cursor.execute(
        "INSERT INTO entries (hash, source, title, link, date) VALUES (?, ?, ?, ?, ?)",
        (hash_val, source, title, link, date)
    )
    conn.commit()
    return True

def get_new_site_links():
    """Return unseen article links from configured websites (HTML scraping)."""
    config = load_config()
    sites = config.get('sites', [])
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)
    new_links = []
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    for site in sites:
        name = site.get('name')
        url = site.get('url')
        selector = site.get('selector', 'a')
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            continue
        soup = BeautifulSoup(resp.text, 'html.parser')
        for a in soup.select(selector):
            link = a.get('href')
            if not link:
                continue
            abs_link = urljoin(url, link)
            entry = {'link': abs_link}
            h = entry_hash(entry)
            if check_and_store(conn, h, name, entry):
                new_links.append({'name': name, 'link': abs_link})
    conn.close()
    return new_links

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

    # Get the most recent article from configured sites
    new_links = get_new_site_links()
    if not new_links:
        print("No new articles found.")
        return
        
    # Process only the most recent article
    feed = new_links[0] if new_links else None
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
            print(article_text[:500] + ("..." if len(article_text) > 500 else ""))
        else:
            if not os.environ.get("OPENAI_API_KEY"):
                print("[ERROR] OPENAI_API_KEY environment variable is not set")
                return
            summary = summarize_text(article_text)
            print("[SUMMARY]")
            print(summary)

if __name__ == "__main__":
    main()
