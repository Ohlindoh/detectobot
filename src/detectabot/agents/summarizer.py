import os
from detectabot.agents.feed_watcher import get_latest_entries
import openai

openai.api_key = os.environ.get("OPENAI_API_KEY")

# Create a basic assistant once (for demo, ephemeral)
ASSISTANT_INSTRUCTIONS = (
    "You are a threat-intel summarisation assistant. "
    "Please summarise the following article in ~200 words, "
    "and list any MITRE ATT&CK technique IDs you find."
)

assistant = openai.beta.assistants.create(
    name="Threat Intel Summarizer",
    instructions=ASSISTANT_INSTRUCTIONS,
    model="gpt-4o"
)

def summarise_text(text: str) -> str:
    """Ask OpenAI agent to produce a 200-word summary with ATT&CK IDs."""
    # Diagnostic: print the text being sent to the agent
    print("\n[DIAGNOSTIC] Text sent to agent:\n" + "-"*40)
    print(text)
    print("-"*40 + "\n")

    # Create a new thread for this summarization
    thread = openai.beta.threads.create()
    # Add the message to the thread
    openai.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=text
    )
    # Run the assistant on the thread
    run = openai.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id
    )
    # Poll for completion
    import time
    while True:
        run_status = openai.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        if run_status.status == "completed":
            break
        time.sleep(0.5)
    # Get the assistant's message
    messages = openai.beta.threads.messages.list(thread_id=thread.id)
    # Find the latest assistant message
    summary = None
    for m in messages:
        if m.role == "assistant":
            summary = m.content[0].text.value
            break
    # Diagnostic: print the raw assistant message
    print("[DIAGNOSTIC] Raw agent response:")
    print(summary)
    print()
    return summary or "[No summary returned]"

if __name__ == "__main__":
    entries = get_latest_entries()
    for item in entries:
        entry = item['entry']
        # Prefer summary or description if available
        text = entry.get('summary') or entry.get('description') or entry.get('title', '')
        print(f"--- Summary for {item['name']} ---")
        print(summarise_text(text))
        print()