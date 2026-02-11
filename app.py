"""
TNega GO Search - Chainlit chat app powered by Gemini File Search.

Usage:
    1. Set GEMINI_API_KEY environment variable
    2. Ensure store_config.json exists (run upload_files.py first)
    3. Run: chainlit run app.py
"""

import json
import os

import chainlit as cl
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

STORE_CONFIG_FILE = "store_config.json"
MODEL = "gemini-2.5-pro"

SYSTEM_PROMPT = (
    "You are a Tamil Nadu Government Orders (GO) search assistant powered by TNe-GA. "
    "You help users find and understand Government Orders issued by the "
    "Information Technology & Digital Services Department of Tamil Nadu.\n\n"
    "When answering:\n"
    "- Always cite the specific GO number, date, and department.\n"
    "- Provide a clear summary of the relevant GO content.\n"
    "- If multiple GOs are relevant, mention all of them.\n"
    "- If the query doesn't match any GO, say so clearly.\n"
    "- Be concise but thorough."
)


def load_store_config() -> str:
    """Load the File Search Store name from config file."""
    if not os.path.exists(STORE_CONFIG_FILE):
        raise FileNotFoundError(
            f"{STORE_CONFIG_FILE} not found. Run upload_files.py first to create the store."
        )
    with open(STORE_CONFIG_FILE) as f:
        config = json.load(f)
    return config["store_name"]


def format_citations(response) -> str:
    """Extract citation info from grounding metadata if available."""
    citations = []
    try:
        grounding = response.candidates[0].grounding_metadata
        if grounding and grounding.grounding_chunks:
            for chunk in grounding.grounding_chunks:
                if chunk.retrieved_context:
                    title = chunk.retrieved_context.title or "Unknown source"
                    if title not in citations:
                        citations.append(title)
    except (AttributeError, IndexError):
        pass

    if citations:
        sources = "\n".join(f"- {c}" for c in citations)
        return f"\n\n---\n**Sources:**\n{sources}"
    return ""


@cl.on_chat_start
async def on_chat_start():
    """Initialize the Gemini client and store name on session start."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        await cl.Message(content="GEMINI_API_KEY environment variable is not set.").send()
        return

    try:
        store_name = load_store_config()
    except FileNotFoundError as e:
        await cl.Message(content=str(e)).send()
        return

    client = genai.Client(api_key=api_key)

    # Store in session for reuse
    cl.user_session.set("client", client)
    cl.user_session.set("store_name", store_name)
    cl.user_session.set("history", [])

    await cl.Message(
        content=(
            "Welcome to **TNe-GA GO Search**!\n\n"
            "I can help you find information from Tamil Nadu Government Orders "
            "issued by the IT & Digital Services Department.\n\n"
            "Try asking:\n"
            '- "What is the cyber security policy?"\n'
            '- "e-Office budget details"\n'
            '- "Data centre policy 2021"\n'
            '- "List all GOs related to ELCOT"'
        )
    ).send()


@cl.on_message
async def on_message(message: cl.Message):
    """Handle user messages by querying Gemini with File Search."""
    client = cl.user_session.get("client")
    store_name = cl.user_session.get("store_name")

    if not client or not store_name:
        await cl.Message(content="Session not initialized. Please refresh the page.").send()
        return

    # Build conversation history with system prompt
    history = cl.user_session.get("history", [])
    contents = [types.Content(role="user", parts=[types.Part(text=SYSTEM_PROMPT)])]
    contents.append(types.Content(role="model", parts=[types.Part(text="Understood. I'm ready to help with Tamil Nadu Government Orders.")]))

    for entry in history:
        contents.append(types.Content(role=entry["role"], parts=[types.Part(text=entry["text"])]))

    contents.append(types.Content(role="user", parts=[types.Part(text=message.content)]))

    # Show thinking step while searching
    async with cl.Step(name="Searching Government Orders...", type="tool") as step:
        step.output = "Looking through GO documents for relevant information..."

        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=contents,
                config=types.GenerateContentConfig(
                    tools=[
                        types.Tool(
                            file_search=types.FileSearch(
                                file_search_store_names=[store_name]
                            )
                        )
                    ],
                ),
            )

            answer = response.text or "I couldn't find a relevant answer."
            citations = format_citations(response)
            full_response = answer + citations
            step.output = "Search complete."

        except Exception as e:
            full_response = f"An error occurred: {e}"
            step.output = f"Search failed: {e}"

    await cl.Message(content=full_response).send()

    # Update conversation history (keep last 10 turns)
    history.append({"role": "user", "text": message.content})
    history.append({"role": "model", "text": full_response})
    if len(history) > 20:
        history = history[-20:]
    cl.user_session.set("history", history)
