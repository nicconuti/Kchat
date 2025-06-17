from models.call_local_llm import call_mistral

def detect_language(user_input: str) -> str:
    """
    Detect the language of the user input using Mistral.

    Returns:
        A two-letter ISO language code (e.g., 'en', 'it', 'fr').
        Defaults to 'en' if detection fails or is unclear.
    """

    prompt = (
        "Detect the language of the following user message.\n"
        "Reply ONLY with the ISO 639-1 language code (like 'en', 'it', 'fr', 'de').\n"
        "No explanation, no punctuation, no space.\n"
        f"Message: \"{user_input}\"\n"
        "Language code:"
    )

    try:
        lang = call_mistral(prompt).strip().lower()
        if len(lang) == 2 and lang.isalpha():
            return lang
        return "en"
    except Exception:
        return "en"
