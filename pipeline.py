from intent_router import detect_intent
from openchat_worker import generate_response
from verifier import verify_response
from clarification_prompt import generate_fallback_question
from language_detector import detect_language
from translator import translate

def run_pipeline(user_input: str):
    lang = detect_language(user_input)
    print(f"[Detected language]: {lang}")

    intent = detect_intent(user_input)
    print(f"[Detected intent]: {intent}")

    if intent is None:
        question = generate_fallback_question(user_input)
        print(f"[Generated clarification]: {question}")
        return question

    response = generate_response(user_input, intent, lang)
    print(f"[Generated response]: {response}")

    detected_resp_lang = detect_language(response)
    if detected_resp_lang != lang:
        response = translate(response, lang)
        print(f"[Translated response]: {response}")

    verified = verify_response(user_input, response)
    print(f"[Response verification]: {'✅ OK' if verified else '❌ INVALID'}")

    return response if verified else generate_fallback_question(user_input)


def run_pipeline_stream(user_input: str):
    """Run the pipeline and stream the final answer after reasoning logs."""
    print("Starting reasoning...")

    lang = detect_language(user_input)
    print(f"[Detected language]: {lang}")

    intent = detect_intent(user_input)
    print(f"[Detected intent]: {intent}")

    if intent is None:
        result = generate_fallback_question(user_input)
        print(f"[Generated clarification]: {result}")
        print("End of reasoning")
        for ch in result:
            yield ch
        return

    response = generate_response(user_input, intent, lang)
    print(f"[Generated response]: {response}")

    detected_resp_lang = detect_language(response)
    if detected_resp_lang != lang:
        response = translate(response, lang)
        print(f"[Translated response]: {response}")

    verified = verify_response(user_input, response)
    print(f"[Response verification]: {'✅ OK' if verified else '❌ INVALID'}")
    if not verified:
        response = generate_fallback_question(user_input)
        print(f"[Fallback question]: {response}")

    print("End of reasoning")
    for ch in response:
        yield ch
