# detectobot

A small proof-of-concept tool for ingesting threat intel feeds and summarizing articles with an LLM.

## Agents

- `summarizer.py` – downloads the latest article from each configured feed and summarizes it with OpenAI.
- `detection_agent.py` – similar to the summarizer but also interprets the article and proposes detection strategies. Pass `--prompt` to experiment with custom system prompts.

Run tests with `pytest`.
