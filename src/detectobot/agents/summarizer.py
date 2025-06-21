"""Threat intelligence summarization agent using Pydantic AI."""
import os
import argparse
from typing import List

import requests
from bs4 import BeautifulSoup
from readability import Document
from pydantic import BaseModel
from pydantic_ai.llm.openai import OpenAIChat
from pydantic_ai.prompt import Prompt

# Allow absolute imports
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from detectobot.core.watcher import get_new_site_links

DEFAULT_PROMPT = (
    "You are a threat-intel assistant for detection engineers. "
    "Summarize the article in about 200 words, identify any MITRE ATT&CK technique IDs, "
    "and provide brief detection tips based on those techniques."
)

class SummaryResponse(BaseModel):
    summary: str
    mitre_ids: List[str]
    detection_tips: str


def analyze_text(text: str, system_prompt: str = DEFAULT_PROMPT) -> SummaryResponse:
    """Send text to the LLM using Pydantic AI and return structured response."""
    llm = OpenAIChat(api_key=os.environ.get("OPENAI_API_KEY"), model="gpt-4o")
    prompt = Prompt(
        system=system_prompt,
        user="""{article_text}

Return your answer with three fields:
- Summary
- MITRE IDs (as a list)
- Detection Tips"""
    )
    return llm(prompt, SummaryResponse, article_text=text)


def fetch_article_text(url: str) -> str:
    """Fetch and return the main text from an article URL."""
    headers = {"User-Agent": "Mozilla/5.0"}
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


def main() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Threat intel summarizer")
    parser.add_argument("--dry-run", action="store_true", help="Preview article text only")
    return parser.parse_args()


if __name__ == "__main__":
    args = main()
    links = get_new_site_links()
    if not links:
        print("No new articles found.")
        exit(0)

    for item in links:
        name = item["name"]
        link = item["link"]
        print(f"\n=== Source: {name} ===")
        print(f"Article URL: {link}")
        text = fetch_article_text(link)
        if args.dry_run:
            print(text[:7000] + ("..." if len(text) > 7000 else ""))
        else:
            result = analyze_text(text)
            print(f"Summary:\n{result.summary}\n")
            print(f"MITRE IDs: {', '.join(result.mitre_ids)}")
            print(f"Detection Tips:\n{result.detection_tips}\n")
