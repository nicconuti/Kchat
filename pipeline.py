from intent_router import detect_intent
from openchat_worker import generate_response
from verifier import verify_response
from clarification_prompt import generate_fallback_question
from language_detector import detect_language

def run_pipeline(user_input: str):
    lang = detect_language(user_input)
    print(f"[Detected language]: {lang}")

    intent = detect_intent(user_input)
    print(f"[Detected intent]: {intent}")

    if intent is None:
        question = generate_fallback_question(user_input)
        print(f"[Generated clarification]: {question}")
        return question

    response = generate_response(user_input, intent)
    print(f"[Generated response]: {response}")

    verified = verify_response(user_input, response)
    print(f"[Response verification]: {'✅ OK' if verified else '❌ INVALID'}")

    return response if verified else generate_fallback_question(user_input)
