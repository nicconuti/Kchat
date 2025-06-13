class Agent:
    """Base class for pipeline agents."""

    def run(self, *args, **kwargs):
        raise NotImplementedError


class LanguageDetectionAgent(Agent):
    def run(self, user_input: str) -> str:
        from language_detector import detect_language

        return detect_language(user_input)


class IntentDetectionAgent(Agent):
    def run(self, user_input: str) -> str | None:
        from intent_router import detect_intent

        return detect_intent(user_input)


class ClarificationAgent(Agent):
    def run(self, user_input: str) -> str:
        from clarification_prompt import generate_fallback_question

        return generate_fallback_question(user_input)


class ResponseGenerationAgent(Agent):
    def run(self, user_input: str, intent: str, lang: str) -> str:
        from openchat_worker import generate_response

        return generate_response(user_input, intent, lang)


class TranslationAgent(Agent):
    def run(self, text: str, target_lang: str) -> str:
        from translator import translate

        return translate(text, target_lang)


class VerificationAgent(Agent):
    def run(self, user_input: str, response: str) -> bool:
        from verifier import verify_response

        return verify_response(user_input, response)

