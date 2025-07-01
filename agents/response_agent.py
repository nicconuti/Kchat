"""Generate the final response for the user."""

from agents.context import AgentContext
from agents.action_agent import run as action_run
from openchat_worker import generate_response
from utils.logger import get_logger


logger = get_logger("chat_log")


def run(context: AgentContext) -> AgentContext:
    """Generate response with strict anti-hallucination measures."""
    
    style = context.formality or "neutral"
    
    # Document-based responses (highest priority and reliability)
    if context.documents and len(context.documents) > 0:
        # Validate document quality before using
        verified_docs = []
        for doc in context.documents:
            if (doc.get('verified_source', False) and 
                doc.get('score', 0) > 0.3 and
                len(doc.get('content', '')) > 20):
                verified_docs.append(doc)
        
        if verified_docs:
            # Use only the best verified document
            best_doc = verified_docs[0]
            
            # Create response based on verified content only
            source = best_doc.get('source', 'fonte sconosciuta')
            content = best_doc.get('content', '')
            category = best_doc.get('category', 'informazione generale')
            
            # Conservative response with clear source attribution
            context.response = f"Basandomi sulle informazioni di {source}:\n\n{content}\n\nFonte: {source}"
            
            # Set reliability based on document quality
            doc_score = best_doc.get('score', 0.5)
            context.source_reliability = min(doc_score * 0.9, 0.85)  # Cap at 0.85 for safety
            
            mode = "doc_verified"
            logger.info(f"Generated response from verified document: {source}")
        else:
            # No verified documents - be honest
            context.response = "Non ho trovato informazioni verificate nella mia knowledge base per rispondere in modo affidabile. Ti consiglio di consultare www.k-array.com per informazioni ufficiali."
            context.source_reliability = 0.0
            mode = "no_verified_docs"
            logger.warning("No verified documents available - providing conservative response")
    
    # Action-based responses (ticket, cost estimation, etc.)
    elif context.intent in {"open_ticket", "cost_estimation", "schedule_appointment", "file_complaint"}:
        try:
            action_run(context)
            # Verify action was successful before claiming it
            if hasattr(context, 'action_results') and context.action_results:
                context.response = f"Ho elaborato la tua richiesta di {context.intent}. Trovi i dettagli nei risultati dell'azione."
                context.source_reliability = 0.8
                mode = "action_completed"
            else:
                context.response = f"Ho ricevuto la tua richiesta di {context.intent} ma non posso confermare se è stata elaborata correttamente. Ti prego di verificare."
                context.source_reliability = 0.4
                mode = "action_uncertain"
        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            context.response = "Si è verificato un errore nell'elaborazione della tua richiesta. Ti prego di riprovare o contattare il supporto."
            context.source_reliability = 0.0
            mode = "action_failed"
    
    # Fallback: conservative general response
    else:
        # Don't generate creative responses - be conservative
        context.response = "Per rispondere accuratamente alla tua domanda, avrei bisogno di informazioni più specifiche dalla knowledge base. Ti consiglio di consultare www.k-array.com per informazioni complete e aggiornate."
        context.source_reliability = 0.1
        mode = "conservative_fallback"
        logger.info("Used conservative fallback response to prevent hallucinations")
        mode = "simple"
    logger.info(
        f"{mode}:{context.response}",
        extra={
            "confidence_score": context.confidence,
            "source_reliability": context.source_reliability,
            "clarification_attempted": context.clarification_attempted,
            "error_flag": context.error_flag,
        },
    )
    return context
