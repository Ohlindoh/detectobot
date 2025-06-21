import os
import argparse
import openai
import time
from detectobot.agents.site_watcher import get_new_article_links
import requests
from bs4 import BeautifulSoup
from readability import Document

DEFAULT_PROMPT = (
    "You are a detection engineering assistant. "
    "Summarize the provided text in about 200 words. "
    "Identify notable behaviors or techniques and propose a detection strategy. "
    "Do not simply list MITRE ATT&CK IDs; interpret the text and recommend detections."
)


def build_assistant(system_prompt: str):
    """Create an OpenAI assistant with the given system prompt."""
    openai.api_key = os.environ.get("OPENAI_API_KEY")
    return openai.beta.assistants.create(
        name="Detection Builder",
        instructions=system_prompt,
        model="gpt-4o",
    )


def analyze_text(text: str, assistant):
    """Send text to the assistant and return the response."""
    thread = openai.beta.threads.create()
    openai.beta.threads.messages.create(thread_id=thread.id, role="user", content=text)
    run = openai.beta.threads.runs.create(thread_id=thread.id, assistant_id=assistant.id)

    while True:
        run_status = openai.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        if run_status.status == "completed":
            break
        time.sleep(1)

    messages = openai.beta.threads.messages.list(thread_id=thread.id)
    for m in messages:
        if m.role == "assistant":
            return m.content[0].text.value
    return "[No response]"


def fetch_article_text(url: str) -> str:
    """Fetch and return main text from an article URL."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            " AppleWebKit/537.36 (KHTML, like Gecko)"
            " Chrome/120.0.0.0 Safari/537.36"
        )
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        try:
            doc = Document(resp.text)
            article_html = doc.summary()
            soup = BeautifulSoup(article_html, "html.parser")
            text = soup.get_text(separator="\n")
            if text.strip():
                return text
            raise ValueError("empty")
        except Exception:
            soup = BeautifulSoup(resp.text, "html.parser")
            paragraphs = soup.find_all("p")
            text = "\n".join(p.get_text() for p in paragraphs)
            if text.strip():
                return text
            return soup.get_text()
    except Exception as e:
        return f"[ERROR fetching article: {e}]"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Detection engineering agent")
    parser.add_argument("--prompt", help="Override system prompt text or path to file")
    parser.add_argument("--dry-run", action="store_true", help="Preview article text only")
    args = parser.parse_args()

    if args.prompt:
        if os.path.isfile(args.prompt):
            system_prompt = open(args.prompt).read()
        else:
            system_prompt = args.prompt
    else:
        system_prompt = DEFAULT_PROMPT

    assistant = build_assistant(system_prompt)

    for feed in get_new_article_links():
        name = feed["name"]
        link = feed["link"]
        print(f"\n=== Feed: {name} ===")
        print(f"Article URL: {link}")
        text = fetch_article_text(link)
        if args.dry_run:
            print(text[:7000] + ("..." if len(text) > 7000 else ""))
        else:
            result = analyze_text(text, assistant)
            print(result)
