# detectobot

A small proof-of-concept tool for ingesting threat intel feeds and summarizing articles with an LLM.

The `config.yaml` file lists websites to watch. Each site entry includes a CSS
selector that identifies article links. The scraper stores seen URLs in a small
SQLite database so each run only processes unseen articles.

## Agents

- `summarizer.py` – downloads any new articles from the configured sites and summarizes them with OpenAI.
- `detection_agent.py` – similar to the summarizer but also interprets the article and proposes detection strategies. Pass `--prompt` to experiment with custom system prompts.

Run tests with `pytest`.
