"""Main orchestration pipeline using modular agents."""

from pipeline_agents import (
    ClarificationAgent,
    IntentDetectionAgent,
    LanguageDetectionAgent,
    ResponseGenerationAgent,
    TranslationAgent,
    VerificationAgent,
)

def run_pipeline(user_input: str):
    lang_detector = LanguageDetectionAgent()
    intent_detector = IntentDetectionAgent()
    clarifier = ClarificationAgent()
    responder = ResponseGenerationAgent()
    translator = TranslationAgent()
    verifier = VerificationAgent()

    lang = lang_detector.run(user_input)
    print(f"[Detected language]: {lang}")

    intent = intent_detector.run(user_input)
    print(f"[Detected intent]: {intent}")

    if intent is None:
        question = clarifier.run(user_input)
        print(f"[Generated clarification]: {question}")
        return question

    response = responder.run(user_input, intent, lang)
    print(f"[Generated response]: {response}")

    detected_resp_lang = lang_detector.run(response)
    if detected_resp_lang != lang:
        response = translator.run(response, lang)
        print(f"[Translated response]: {response}")

    verified = verifier.run(user_input, response)
    print(f"[Response verification]: {'✅ OK' if verified else '❌ INVALID'}")

    return response if verified else clarifier.run(user_input)


def run_pipeline_stream(user_input: str):
    """Run the pipeline and stream the final answer after reasoning logs."""
    print("Starting reasoning...")

    lang_detector = LanguageDetectionAgent()
    intent_detector = IntentDetectionAgent()
    clarifier = ClarificationAgent()
    responder = ResponseGenerationAgent()
    translator = TranslationAgent()
    verifier = VerificationAgent()

    lang = lang_detector.run(user_input)
    print(f"[Detected language]: {lang}")

    intent = intent_detector.run(user_input)
    print(f"[Detected intent]: {intent}")

    if intent is None:
        result = clarifier.run(user_input)
        print(f"[Generated clarification]: {result}")
        print("End of reasoning")
        for ch in result:
            yield ch
        return

    response = responder.run(user_input, intent, lang)
    print(f"[Generated response]: {response}")

    detected_resp_lang = lang_detector.run(response)
    if detected_resp_lang != lang:
        response = translator.run(response, lang)
        print(f"[Translated response]: {response}")

    verified = verifier.run(user_input, response)
    print(f"[Response verification]: {'✅ OK' if verified else '❌ INVALID'}")
    if not verified:
        response = clarifier.run(user_input)
        print(f"[Fallback question]: {response}")

    print("End of reasoning")
    for ch in response:
        yield ch
