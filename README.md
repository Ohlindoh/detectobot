# detectobot

A small proof-of-concept tool for ingesting threat intel feeds and summarizing articles with an LLM.

The `config.yaml` file lists websites to watch. Each site entry includes a CSS
selector that identifies article links. The scraper stores seen URLs in a small
SQLite database so each run only processes unseen articles.

## Agents

- `summarizer.py` – processes a URL or new site links and outputs a DetectionSpec JSON using Pydantic AI.
- `detection_agent.py` – similar to the summarizer but also interprets the article and proposes detection strategies. Pass `--prompt` to experiment with custom system prompts.

Install dependencies using [uv](https://github.com/astral-sh/uv) and run the tests with `pytest`.

```bash
uv pip install -r requirements.txt
pytest
```

## Development

Install dependencies with [uv](https://github.com/astral-sh/uv):

```bash
uv pip install -r requirements.txt
```

Run the tools directly once dependencies are installed, e.g.

```bash
python -m detectobot.agents.summarizer
```
