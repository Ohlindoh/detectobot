import os
import argparse
from pydantic import BaseModel
from pydantic_ai.llm.openai import OpenAIChat
from pydantic_ai.prompt import Prompt
import time
from detectobot.watcher import get_new_feed_links, get_new_site_links
import requests
from bs4 import BeautifulSoup
from readability import Document

DEFAULT_PROMPT = (
    "You are a detection engineering assistant. "
    "Summarize the provided text in about 200 words. "
    "Identify notable behaviors or techniques and propose a detection strategy. "
    "Do not simply list MITRE ATT&CK IDs; interpret the text and recommend detections."
)


class DetectionResponse(BaseModel):
    summary: str
    detection_strategy: str


def analyze_text(text: str, system_prompt: str) -> DetectionResponse:
    """Send text to the LLM using Pydantic AI and return structured response."""
    llm = OpenAIChat(
        api_key=os.environ.get("OPENAI_API_KEY"),
        model="gpt-4o"
    )
    prompt = Prompt(
        system=system_prompt,
        user="""{article_text}

Return your answer as two sections:
- Summary: A concise summary (~200 words)
- Detection Strategy: Your recommended detection strategy"""
    )
    response = llm(
        prompt,
        DetectionResponse,
        article_text=text
    )
    return response





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

    parser.add_argument("--source", choices=["feed", "site"], default="feed", help="Source type: feed (RSS) or site (HTML)")
    args = parser.parse_args()

    if args.source == "feed":
        sources = get_new_feed_links()
    else:
        sources = get_new_site_links()

    for item in sources:
        name = item["name"]
        link = item["link"]
        print(f"\n=== Source: {name} ===")
        print(f"Article URL: {link}")
        text = fetch_article_text(link)
        if args.dry_run:
            print(text[:7000] + ("..." if len(text) > 7000 else ""))
        else:
            result = analyze_text(text, system_prompt)
            print(f"Summary:\n{result.summary}\n")
            print(f"Detection Strategy:\n{result.detection_strategy}\n")
