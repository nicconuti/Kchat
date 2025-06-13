from models.mistral import call_mistral

def detect_intent(user_input: str) -> str:
    prompt = f"""Classifica l'intento di questa frase utente: "{user_input}"
Restituisci solo uno tra: crea_preventivo, recupera_documento, apri_ticket, prenota_intervento, generico."""
    return call_mistral(prompt)
