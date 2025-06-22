# detectobot

A small proof-of-concept tool for ingesting threat intel feeds and summarizing articles with an LLM.

The `config.yaml` file lists websites to watch. Each site entry includes a CSS
selector that identifies article links. The scraper stores seen URLs in a small
SQLite database so each run only processes unseen articles.

## Agents

- `summarizer.py` – processes a URL or new site links and outputs a DetectionSpec JSON using Pydantic AI.
- `detection_agent.py` – similar to the summarizer but also interprets the article and proposes detection strategies. Pass `--prompt` to experiment with custom system prompts.

Run tests with `poetry run pytest`.

## Development

Install dependencies with [Poetry](https://python-poetry.org/):

```bash
poetry install
```

Run tools through Poetry, e.g.

```bash
poetry run python -m detectobot.agents.summarizer
```
