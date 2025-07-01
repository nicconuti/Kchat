"""Simple rule-based orchestrator."""

from agents.context import AgentContext
from agents.language_agent import run as detect_language
from agents.intent_agent import run as detect_intent
from agents.document_retriever_agent import run as retrieve
from agents.response_agent import run as generate_response
from agents.clarification_agent import run as clarify
from agents.translation_agent import run as translate
from translator import translate as translate_text
from agents.verification_agent import run as verify
from models.call_local_llm import call_mistral
from utils.logger import get_logger
import json


logger = get_logger("orchestration_trace")


_STEP_MAP = {
    "language": detect_language,
    "intent": detect_intent,
    "retrieve": retrieve,
    "respond": generate_response,
    "clarify": clarify,
}


def _fallback_sequence(context: AgentContext):
    if "quote" in context.input.lower():
        seq = ["language", "intent", "retrieve", "respond"]
        reasoning = "fallback: quote request"
    else:
        seq = ["language", "intent", "respond"]
        reasoning = "fallback: default"
    return reasoning, [
        _STEP_MAP[name] for name in seq if name in _STEP_MAP
    ]


def choose_agent_sequence(context: AgentContext):
    prompt = (
        "You are an orchestrator deciding which agents to run."
        " Available agents: language, intent, retrieve, respond."
        " Based on the user message, output a JSON object with keys"
        " 'reasoning' (string) and 'sequence' (list of agent names)."
        f" User message: {context.input!r}\nJSON:"
    )

    try:
        raw = call_mistral(prompt)
        data = json.loads(raw)
        context.reasoning_trace = data.get("reasoning", "")
        seq_names = data.get("sequence", [])
        seq = [_STEP_MAP.get(n) for n in seq_names if n in _STEP_MAP]
        if not seq:
            raise ValueError("empty sequence")
    except Exception:
        context.reasoning_trace, seq = _fallback_sequence(context)

    logger.info(
        context.reasoning_trace,
        extra={
            "confidence_score": context.confidence,
            "source_reliability": context.source_reliability,
            "clarification_attempted": context.clarification_attempted,
            "error_flag": context.error_flag,
        },
    )

    return seq



def run(context: AgentContext) -> AgentContext:
    """
    Orchestrate the agent pipeline with enhanced error recovery and fallback mechanisms.
    """
    # Initialize error tracking
    execution_errors = []
    recovered_from_errors = 0
    
    try:
        # Add user input to conversation history
        context.conversation_history.append(("user", context.input))
        original_input = context.input
        
        # Execute agent sequence with error recovery
        agent_sequence = choose_agent_sequence(context)
        
        for i, step in enumerate(agent_sequence):
            step_name = step.__name__ if hasattr(step, '__name__') else f"step_{i}"
            
            try:
                logger.debug(f"Executing agent step: {step_name}")
                
                # Special handling for intent detection with translation
                if step is detect_intent:
                    try:
                        # Attempt translation if needed
                        if context.language != "en":
                            pivot_text = translate_text(context.input, "en")
                            if not pivot_text or pivot_text == context.input:
                                logger.warning("Translation failed or unnecessary, using original text")
                                pivot_text = context.input
                        else:
                            pivot_text = context.input
                            
                        context.input = pivot_text
                        step(context)
                        context.input = original_input
                        
                    except Exception as e:
                        logger.error(f"Translation or intent detection failed: {e}")
                        execution_errors.append(f"intent_detection: {str(e)}")
                        
                        # Fallback: use original input without translation
                        context.input = original_input
                        try:
                            step(context)
                            recovered_from_errors += 1
                            logger.info("Recovered from translation error using original input")
                        except Exception as e2:
                            logger.error(f"Intent detection fallback also failed: {e2}")
                            context.error_flag = True
                            break
                else:
                    # Execute other agents with error handling
                    step(context)
                
                # Check for critical errors that should stop execution
                if context.error_flag:
                    logger.warning(f"Error flag set by {step_name}, stopping pipeline")
                    break
                    
            except Exception as e:
                step_error = f"{step_name}: {str(e)}"
                execution_errors.append(step_error)
                logger.error(f"Agent step {step_name} failed: {e}", exc_info=True)
                
                # Attempt to continue with degraded functionality
                if step_name in ['language', 'translation']:
                    # Non-critical errors, continue with defaults
                    logger.info(f"Continuing after non-critical error in {step_name}")
                    recovered_from_errors += 1
                    continue
                elif step_name in ['retrieve', 'document_retriever']:
                    # Document retrieval failed, continue without documents
                    logger.warning("Document retrieval failed, continuing without retrieved documents")
                    context.documents = []
                    recovered_from_errors += 1
                    continue
                else:
                    # Critical error, stop execution
                    logger.error(f"Critical error in {step_name}, stopping pipeline")
                    context.error_flag = True
                    break

        # Handle post-execution logic with enhanced anti-hallucination measures
        try:
            # Check source reliability before response generation
            if hasattr(context, 'source_reliability') and context.source_reliability < 0.3:
                logger.warning(f"Low source reliability ({context.source_reliability:.2f}) detected")
                
                # If we have no reliable sources, provide honest response
                if context.source_reliability == 0.0 or not context.documents:
                    context.response = "Non ho trovato informazioni affidabili nella knowledge base per rispondere alla tua domanda. Ti consiglio di consultare direttamente il sito ufficiale www.k-array.com per informazioni aggiornate."
                    context.source_reliability = 0.0
                    context.confidence = 0.0
                    logger.info("Provided 'no information found' response to prevent hallucinations")
                
                # If reliability is very low, add disclaimer
                elif context.source_reliability < 0.4 and context.response:
                    context.response += "\n\nNota: Le informazioni fornite potrebbero non essere complete. Per dettagli aggiornati consulta www.k-array.com"
                    logger.info("Added disclaimer due to low source reliability")

            # Intent clarification if needed
            if context.intent is None and not context.error_flag:
                logger.info("No intent detected, attempting clarification")
                try:
                    clarify(context)
                except Exception as e:
                    logger.error(f"Clarification failed: {e}")
                    execution_errors.append(f"clarification: {str(e)}")
                    # Provide fallback response
                    context.response = "Mi dispiace, non sono riuscito a comprendere la tua richiesta. Potresti riformularla in modo più specifico?"
                    context.source_reliability = 0.0

            # Response verification with enhanced checks
            elif context.response and not context.error_flag:
                try:
                    # Only verify if we have reasonable source reliability
                    if context.source_reliability > 0.3:
                        if not verify(context):
                            logger.warning("Response verification failed")
                            # Instead of clarification, be conservative
                            context.response = "Non posso fornire una risposta affidabile a questa domanda. Ti consiglio di consultare www.k-array.com per informazioni accurate."
                            context.source_reliability = 0.0
                            logger.info("Replaced unverified response with conservative message")
                    else:
                        logger.info("Skipping verification due to low source reliability")
                        
                except Exception as e:
                    logger.error(f"Verification failed: {e}")
                    execution_errors.append(f"verification: {str(e)}")
                    # Be conservative on verification errors
                    context.response = "Si è verificato un errore nella verifica della risposta. Per sicurezza, ti invito a consultare www.k-array.com per informazioni accurate."
                    context.source_reliability = 0.0

            # Final translation with error recovery
            try:
                translate(context, context.language)
            except Exception as e:
                logger.error(f"Final translation failed: {e}")
                execution_errors.append(f"final_translation: {str(e)}")
                # If translation fails, at least ensure we have some response
                if not context.response:
                    context.response = "Errore nel sistema di traduzione. Scusa per il disagio."

        except Exception as e:
            logger.error(f"Post-execution error: {e}", exc_info=True)
            execution_errors.append(f"post_execution: {str(e)}")

        # Ensure we always have a response
        if not context.response:
            context.response = "Mi dispiace, si è verificato un errore interno. Ti preghiamo di riprovare."
            context.error_flag = True
            context.source_reliability = 0.0

        # Add assistant response to conversation history
        context.conversation_history.append(("assistant", context.response or ""))

        # Log orchestration completion with error summary
        logger.info(
            "orchestration complete",
            extra={
                "confidence_score": context.confidence,
                "source_reliability": context.source_reliability,
                "clarification_attempted": context.clarification_attempted,
                "error_flag": context.error_flag,
                "execution_errors": len(execution_errors),
                "recovered_errors": recovered_from_errors,
                "error_details": execution_errors if execution_errors else None
            },
        )

        # Log error summary if there were issues
        if execution_errors:
            logger.warning(f"Pipeline completed with {len(execution_errors)} errors, {recovered_from_errors} recovered")
        
        return context
        
    except Exception as e:
        # Catastrophic failure handling
        logger.critical(f"Catastrophic orchestration failure: {e}", exc_info=True)
        
        # Ensure context is in a valid state
        context.error_flag = True
        context.source_reliability = 0.0
        
        if not context.response:
            context.response = "Si è verificato un errore critico del sistema. Contatta l'assistenza tecnica."
        
        # Still add to conversation history for continuity
        if ("user", context.input) not in context.conversation_history:
            context.conversation_history.append(("user", context.input))
        context.conversation_history.append(("assistant", context.response))
        
        logger.error(
            "catastrophic orchestration failure",
            extra={
                "error_flag": True,
                "source_reliability": 0.0,
                "critical_error": str(e)
            },
        )
        
        return context
