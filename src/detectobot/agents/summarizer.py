"""ThreatIntel2Detection summarizer using Pydantic AI."""
import os
import argparse

import requests
from bs4 import BeautifulSoup
from readability import Document
from pydantic import BaseModel, HttpUrl
from pydantic_ai import Agent

# Allow absolute imports for watcher utilities
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from detectobot.core.watcher import get_new_site_links

DEFAULT_PROMPT = ("""
    You are “ThreatIntel2Detection”, an expert LLM assistant that ingests public cyber-threat-intelligence documents and converts them into high-quality, production-ready detection specifications.

    ### 1. Mission
    Transform any intel report into a JSON **DetectionSpec** (see §6) that detection engineers can drop into a Detection-as-Code pipeline without additional formatting.

    ### 2. Required reasoning steps (think, then only output the final JSON)
    1. **Read & comprehend** the entire source; do not skim.  
    2. **Extract metadata**: article_title, source_url, publication_date, threat_actor.  
    3. **Parse TTPs**  
    • Map each to ATT&CK tactic, technique, sub-technique following CISA mapping best-practices.  
    • Capture procedure-level detail (commands, registry keys, HTTP headers, etc.).  
    4. **Assess detectability_confidence** for each TTP:  
    • `high` → narrow, low-FP logic likely (Sigma `critical`/`high`).  
    • `medium` → moderate tuning expected.  
    • `low` → heuristic or noisy; useful mainly for hunting.  
    • Record a one-sentence `confidence_reason`.  
    5. **Draft detection logic** for each TTP:  
    • **Telemetry requirements** (logsource & required fields).  
    • **Sigma stub** (`sigma_yaml`): title, logsource, detection, condition, ATT&CK tags, falsepositives placeholders.  
    • **False-positive analysis**: list two likely benign scenarios.  
    6. **Output a DetectionSpec JSON** conforming exactly to §6.

    ### 3. Voice & style
    • Be concise, plain language.  
    • Use ISO dates (YYYY-MM-DD) & ATT&CK IDs (Txxxx).  
    • No extra prose—return only the JSON, preceded by `### DetectionSpec`.

    ### 4. Guardrails
    • Never guess ATT&CK mappings; if uncertain mark `confidence_reason` accordingly.  
    • Omit stale indicators (> 18 months old) unless evidence shows ongoing activity.  
    • Flag visibility gaps in `prerequisites`.  
    • If intel lacks detail, set `status` = `insufficient_detail` and summarise missing pieces.
    • Don't hallucinate.

    ### 5. Error handling
    If validation of the JSON against the schema would fail, retry once internally; otherwise return `status` = `insufficient_detail`.

    ### 6. JSON schema
    class SigmaStub(BaseModel):
        title: str
        id: str
        logsource: Dict[str, str]
        detection: Dict[str, Any]
        condition: str
        tags: List[str]
        falsepositives: List[str]

    class TTPEntry(BaseModel):
        tactic: str
        technique: str
        subtechnique: Optional[str]
        description: str
        detectability_confidence: Literal["high","medium","low"]
        confidence_reason: str  # brief rationale
        sigma_stub: SigmaStub
        validation: List[str]    # Atomic IDs or scripts
        falsepositive_notes: List[str]

    class DetectionSpec(BaseModel):
        article_title: str
        source_url: HttpUrl
        publication_date: date
        threat_actor: Optional[str]
        ttps: List[TTPEntry]
        prerequisites: List[str]  # telemetry gaps, tooling needs
        notes: str
        status: Literal["draft","ready","insufficient_detail"]

    """
)


class SigmaStub(BaseModel):
    title: str
    id: str
    logsource: dict[str, str]
    detection: dict[str, str | list | dict]
    condition: str
    tags: list[str]
    falsepositives: list[str]


class TTPEntry(BaseModel):
    tactic: str
    technique: str
    subtechnique: str | None
    description: str
    detectability_confidence: str
    confidence_reason: str
    sigma_stub: SigmaStub
    validation: list[str]
    falsepositive_notes: list[str]


class DetectionSpec(BaseModel):
    article_title: str
    source_url: HttpUrl
    publication_date: str
    threat_actor: str | None
    ttps: list[TTPEntry]
    prerequisites: list[str]
    notes: str
    status: str

def analyze_text(text: str, system_prompt: str = DEFAULT_PROMPT) -> DetectionSpec:
    """Send text to the LLM and parse the DetectionSpec."""
    agent = Agent(
        "openai:gpt-4o",
        system_prompt=system_prompt,
        output_type=DetectionSpec,
    )
    result = agent.run_sync(
        f"Here is the article text:\n\n{text}",
    )
    return result.output


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
    """Parse command-line arguments for the summarizer utility."""
    parser = argparse.ArgumentParser(description="Summarize a threat intel article")
    parser.add_argument("url", nargs="?", help="Article URL to process")
    parser.add_argument("--prompt", help="Override system prompt text or path to file")
    parser.add_argument("--dry-run", action="store_true", help="Print article text only")
    return parser.parse_args()


if __name__ == "__main__":
    args = main()
    system_prompt = DEFAULT_PROMPT
    if args.prompt:
        if os.path.isfile(args.prompt):
            system_prompt = open(args.prompt).read()
        else:
            system_prompt = args.prompt

    if args.url:
        sources = [{"name": "manual", "link": args.url}]
    else:
        sources = get_new_site_links()
        if not sources:
            print("No new articles found.")
            exit(0)

    for item in sources:
        link = item["link"]
        text = fetch_article_text(link)
        if args.dry_run:
            print(text)
        else:
            spec = analyze_text(text, system_prompt)
            print(spec.model_dump_json(indent=2))
