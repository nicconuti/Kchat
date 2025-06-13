from models.openchat import call_openchat


def generate_response(user_input: str, intent: str) -> str:
    """Generate a helpful answer using OpenChat."""

    prompt = (
        f"The user asked: {user_input}\n"
        f"Detected intent: {intent}.\n"
        "Provide a clear, helpful response."
    )
    return call_openchat(prompt)
