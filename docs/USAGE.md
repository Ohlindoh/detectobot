# Usage Guide

This document outlines common workflows when using **detectobot**.

Install dependencies with [uv](https://github.com/astral-sh/uv):

```bash
uv pip install -r requirements.txt
```

## Configuration

Edit `config.yaml` to list RSS feeds or websites you want to monitor. Each
website entry may specify a CSS selector so the scraper can locate article
links.

## Running the Tools

### Summarizer

Fetch the latest unseen articles from configured websites and output a
structured `DetectionSpec` JSON:

```bash
python -m detectobot.agents.summarizer
```

Pass a specific URL to summarize just one article:

```bash
python -m detectobot.agents.summarizer https://example.com/post
```

### Detection Agent

Generate both a summary and recommended detection strategy for each new
article:

```bash
python -m detectobot.agents.detection_agent --source site
```

Use `--dry-run` to print the raw article text without contacting the LLM.
