import os

def run_openai(user_text: str, model: str) -> str:
    """
    Uses the OpenAI Python SDK Responses API.
    """
    from openai import OpenAI

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    client = OpenAI(api_key=api_key)

    # The OpenAI Python SDK shows `client.responses.create(...)` as the primary interface. :contentReference[oaicite:2]{index=2}
    resp = client.responses.create(
        model=model,
        input=user_text,
    )
    return resp.output_text


def run_anthropic(user_text: str, model: str) -> str:
    """
    Uses the Anthropic Python SDK Messages API.
    """
    from anthropic import Anthropic

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")

    client = Anthropic(api_key=api_key)

    # Anthropic SDK usage pattern: client.messages.create(...). :contentReference[oaicite:3]{index=3}
    msg = client.messages.create(
        model=model,
        max_tokens=2048,
        messages=[{"role": "user", "content": user_text}],
    )

    # SDK returns a list of content blocks; we want plain text
    parts = []
    for block in msg.content:
        if getattr(block, "type", None) == "text":
            parts.append(block.text)
    return "\n".join(parts).strip()