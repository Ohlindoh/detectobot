import os, requests, feedparser
from typing import Optional
import openai

# Load API key
openai.api_key = os.environ.get("OPENAI_API_KEY")

def fetch_latest_entry(feed_url: str) -> Optional[feedparser.FeedParserDict]:
    """Return the most recent entry from the given RSS/Atom URL."""
    feed = feedparser.parse(feed_url)
    return feed.entries[0] if feed.entries else None

def extract_content(entry: feedparser.FeedParserDict) -> str:
    """Fetch the full article HTML and return plaintext."""
    resp = requests.get(entry.link, timeout=10)
    # Naïve strip; you can swap in BeautifulSoup later
    return resp.text

def summarise_text(text: str) -> str:
    """Ask OpenAI to produce a 200‑word summary with ATT&CK IDs."""
    prompt = (
        "You are a threat‑intel summarisation assistant.\n"
        "Please summarise the following article in ~200 words, "
        "and list any MITRE ATT&CK technique IDs you find:\n\n"
        + text
    )
    resp = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role":"user", "content":prompt}],
        temperature=0.2,
        max_tokens=500,
    )
    return resp.choices[0].message.content.strip()

if __name__ == "__main__":
    # Load your first feed from config.yaml
    import yaml
    cfg = yaml.safe_load(open("config.yaml"))
    feed = cfg["feeds"][0]["url"]   # e.g. CISA Advisories&#8203;:contentReference[oaicite:2]{index=2}&#8203;:contentReference[oaicite:3]{index=3}
    
    entry = fetch_latest_entry(feed)
    if not entry:
        print("No entries found.")
        exit(1)
    
    print(f"▶️ Summarising: {entry.title}\nLink: {entry.link}\n")
    article = extract_content(entry)
    summary = summarise_text(article)
    print("\n📝 Summary:\n", summary)
    