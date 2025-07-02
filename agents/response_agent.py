"""Generate the final response for the user."""

from agents.context import AgentContext
from agents.action_agent import run as action_run
from openchat_worker import generate_response
from models.call_local_llm import call_mistral
from utils.logger import get_logger
from typing import List, Dict, Any, Optional
import re


logger = get_logger("chat_log")


def _extract_key_info(content: str, topic: str) -> str:
    """Extract key information about a specific topic from document content, avoiding cross-contamination."""
    # Split content into sentences/sections
    sentences = re.split(r'[.!?]+|\n+', content)
    relevant_sentences = []
    
    # Look for sentences containing the topic
    topic_lower = topic.lower()
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) > 10 and topic_lower in sentence.lower():
            # Additional filter: avoid mixing product information
            # If looking for K-Framework, exclude sentences that primarily describe hardware
            if 'k-framework' in topic_lower:
                # Skip sentences that are primarily about hardware specs
                if any(hw_term in sentence.lower() for hw_term in ['woofer', 'amplifier', 'transducer', 'ohm', 'watt', 'spl']):
                    continue
            relevant_sentences.append(sentence)
    
    # Take most relevant sentences (up to 5 for comprehensive info)
    if relevant_sentences:
        return '. '.join(relevant_sentences[:5]) + '.'  # Increased for better detail
    else:
        # If no specific sentences found, return a larger excerpt for context
        return content[:600] + '...' if len(content) > 600 else content


def _generate_intelligent_response(context: AgentContext, documents: List[Dict[str, Any]]) -> Optional[str]:
    """Generate an intelligent, natural response based on user query and retrieved documents."""
    
    user_query = context.input.lower()
    intent = context.intent or "information_request"
    
    # Extract key information from documents
    doc_summaries = []
    sources = []
    
    for doc in documents[:4]:  # Use top 4 documents for more comprehensive info
        content = doc.get('content', '')
        source = doc.get('source', 'k-array.com')
        
        # Extract relevant content based on query
        if 'k-framework' in user_query:
            key_info = _extract_key_info(content, 'k-framework')
        elif 'k-array' in user_query:
            key_info = _extract_key_info(content, 'k-array')
        else:
            key_info = content[:800]  # Take more content for better context
        
        doc_summaries.append(key_info)
        sources.append(source)
    
    # Create a natural language prompt for the LLM
    prompt = f"""Genera una risposta naturale e professionale alla domanda dell'utente basandoti ESCLUSIVAMENTE sulle informazioni fornite. NON INVENTARE O DEDURRE NULLA.

Domanda dell'utente: {context.input}
Intenzione: {intent}

Informazioni disponibili:
{chr(10).join(f"- {summary}" for summary in doc_summaries)}

Fonti: {', '.join(sources)}

REGOLE CRITICHE ANTI-ALLUCINAZIONE:
1. USA SOLO le informazioni ESPLICITAMENTE presenti nel testo fornito
2. NON collegare prodotti diversi tra loro se non specificato nel testo
3. NON attribuire caratteristiche di un prodotto ad un altro
4. NON inventare specifiche tecniche o dettagli non presenti
5. Se chiedi di un prodotto specifico, parla SOLO di quel prodotto
6. Se le informazioni sono limitate, dillo chiaramente invece di inventare
7. NON mescolare informazioni da documenti diversi su prodotti diversi
8. Mantieni separati i contesti di prodotti diversi

ESEMPIO SBAGLIATO: "K-Framework3 è dotato del Thunder-KS5 I" (mescolamento)
ESEMPIO CORRETTO: "K-Framework3 è un software. Nelle fonti sono menzionati anche altri prodotti come Thunder-KS5 I, ma sono prodotti separati"

Se non hai informazioni sufficienti per una risposta completa, rispondi: "Le informazioni disponibili indicano che [quello che sai], ma per dettagli completi consultare la documentazione ufficiale."

Risposta:"""

    try:
        response = call_mistral(prompt)
        if response and len(response.strip()) > 20:
            # Add source attribution
            response_with_source = f"{response.strip()}\n\n📄 Fonte: {sources[0]}"
            return response_with_source
        else:
            logger.warning("LLM generated empty or too short response")
            return None
    except Exception as e:
        logger.error(f"Error generating intelligent response: {e}")
        return None


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
            # Generate intelligent response based on context and documents
            try:
                smart_response = _generate_intelligent_response(context, verified_docs)
                if smart_response:
                    context.response = smart_response
                    # Set reliability based on document quality and response confidence
                    doc_score = verified_docs[0].get('score', 0.5)
                    context.source_reliability = min(doc_score * 0.9, 0.85)
                    mode = "intelligent_response"
                    logger.info(f"Generated intelligent response from {len(verified_docs)} documents")
                else:
                    # Fallback to simple document content
                    best_doc = verified_docs[0]
                    source = best_doc.get('source', 'fonte sconosciuta')
                    content = best_doc.get('content', '')
                    context.response = f"Basandomi sulle informazioni di {source}:\n\n{content}\n\nFonte: {source}"
                    doc_score = best_doc.get('score', 0.5)
                    context.source_reliability = min(doc_score * 0.9, 0.85)
                    mode = "doc_verified"
                    logger.info(f"Generated fallback response from verified document: {source}")
            except Exception as e:
                logger.error(f"Intelligent response generation failed: {e}")
                # Fallback to simple document content
                best_doc = verified_docs[0]
                source = best_doc.get('source', 'fonte sconosciuta')
                content = best_doc.get('content', '')
                context.response = f"Basandomi sulle informazioni di {source}:\n\n{content}\n\nFonte: {source}"
                doc_score = best_doc.get('score', 0.5)
                context.source_reliability = min(doc_score * 0.9, 0.85)
                mode = "doc_verified_fallback"
                logger.info(f"Generated fallback response from verified document: {source}")
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
