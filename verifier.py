from models.mistral import call_mistral

def verify_response(user_input: str, response: str) -> bool:
    prompt = f"""Risposta: "{response}"\nDomanda: "{user_input}"\n
Valuta se la risposta è pertinente e utile. Rispondi solo con: TRUE o FALSE."""
    result = call_mistral(prompt)
    return "TRUE" in result.upper()
