from intent_router import detect_intent
from openchat_worker import generate_response
from verifier import verify_response
from language_detector import detect_language

def run_pipeline(user_input: str):
    lang = detect_language(user_input)
    print(f"[Lingua rilevata]: {lang}")

    intent = detect_intent(user_input)
    print(f"[Intent rilevato]: {intent}")

    response = generate_response(user_input, intent)
    print(f"[Risposta generata]: {response}")

    verified = verify_response(user_input, response)
    print(f"[Verifica risposta]: {'✅ OK' if verified else '❌ NON valida'}")

    return response if verified else "⚠️ La risposta non è stata validata. Riformula la domanda."
