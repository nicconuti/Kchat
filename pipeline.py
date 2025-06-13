from intent_router import detect_intent
from openchat_worker import generate_response, generate_response_stream
from verifier import verify_response
from clarification_prompt import generate_fallback_question
from language_detector import detect_language
from translator import translate, translate_stream

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
    """Run the pipeline yielding tokens as soon as they are produced."""
    lang = detect_language(user_input)
    print(f"[Detected language]: {lang}")

    intent = detect_intent(user_input)
    print(f"[Detected intent]: {intent}")

    if intent is None:
        question = generate_fallback_question(user_input)
        print(f"[Generated clarification]: {question}")
        yield question
        return

    stream = generate_response_stream(user_input, intent, lang)
    collected = []
    for token in stream:
        collected.append(token)
        yield token
    response = "".join(collected)

    detected_resp_lang = detect_language(response)
    if detected_resp_lang != lang:
        translated_tokens = list(translate_stream(response, lang))
        response = "".join(translated_tokens)
        print(f"[Translated response]: {response}")
        for t in translated_tokens:
            yield t

    verified = verify_response(user_input, response)
    print(f"[Response verification]: {'✅ OK' if verified else '❌ INVALID'}")
    if not verified:
        fallback = generate_fallback_question(user_input)
        print(f"[Fallback question]: {fallback}")
        yield fallback
