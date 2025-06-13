from models.mistral import call_mistral


def verify_response(user_input: str, response: str) -> bool:
    """Check whether the answer is relevant and helpful."""

    prompt = (
        f"Answer: \"{response}\"\n"
        f"Question: \"{user_input}\"\n"
        "Evaluate if the answer is relevant and helpful. Respond only with: TRUE or FALSE."
    )
    result = call_mistral(prompt)
    return "TRUE" in result.upper()
