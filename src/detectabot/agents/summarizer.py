import os
from detectabot.agents.feed_watcher import get_latest_entries
from openai import OpenAI

# Initialize client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Update the API call
def summarise_text(text: str) -> str:
    """Ask OpenAI to produce a 200‑word summary with ATT&CK IDs."""
    prompt = (
        "You are a threat‑intel summarisation assistant.\n"
        "Please summarise the following article in ~200 words, "
        "and list any MITRE ATT&CK technique IDs you find:\n\n"
        + text
    )
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role":"user", "content":prompt}],
        temperature=0.2,
        max_tokens=500,
    )
    return resp.choices[0].message.content.strip()

if __name__ == "__main__":
    entries = get_latest_entries()
    for item in entries:
        entry = item['entry']
        # Prefer summary or description if available
        text = entry.get('summary') or entry.get('description') or entry.get('title', '')
        print(f"--- Summary for {item['name']} ---")
        print(summarise_text(text))
        print()