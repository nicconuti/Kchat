from intent_router import detect_intent
from openchat_worker import generate_response
from verifier import verify_response
from language_detector import detect_language

def run_pipeline(user_input: str):
    lang = detect_language(user_input)
    print(f"[Detected language]: {lang}")

    intent = detect_intent(user_input)
    print(f"[Detected intent]: {intent}")

    response = generate_response(user_input, intent)
    print(f"[Generated response]: {response}")

    verified = verify_response(user_input, response)
    print(f"[Response verification]: {'✅ OK' if verified else '❌ INVALID'}")

    return response if verified else "⚠️ The answer was not validated. Please rephrase your question."
