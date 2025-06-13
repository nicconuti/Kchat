from models.openchat import call_openchat

def generate_response(user_input: str, intent: str) -> str:
    prompt = f"L'utente ha chiesto: {user_input}\nIntent rilevato: {intent}.\nRispondi in modo utile e chiaro."
    return call_openchat(prompt)
