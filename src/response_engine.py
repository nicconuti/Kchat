#!/usr/bin/env python3
"""
Response Engine for K-Array Chat System
Zero-hallucination response generation with source attribution and dual LLM fallback
"""

import logging
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from src.llm_manager import LLMManager
from src.smart_retriever import RetrievalContext


@dataclass
class ResponseMetrics:
    """Metrics for response quality tracking"""
    confidence_score: float
    source_count: int
    technical_accuracy: float
    completeness: float
    response_time: float
    llm_provider_used: str
    fallback_triggered: bool


class ResponseEngine:
    """Zero-hallucination response engine with dual LLM support"""
    
    def __init__(self, primary_provider: str = "gemini", fallback_provider: str = "openai"):
        self.primary_llm = LLMManager(primary_provider)
        self.fallback_llm = LLMManager(fallback_provider)
        self.setup_logging()
        
        # Response templates for different query types
        self.response_templates = {
            'technical': self._get_technical_template(),
            'application': self._get_application_template(),
            'comparison': self._get_comparison_template(),
            'general': self._get_general_template()
        }
        
        # Quality thresholds
        self.min_confidence = 0.7
        self.min_sources = 2
    
    def setup_logging(self):
        """Setup logging"""
        self.logger = logging.getLogger(__name__)
    
    def _get_technical_template(self) -> str:
        """Template for technical specification responses"""
        return """
        Sei un esperto tecnico K-Array. Rispondi alla domanda usando SOLO le informazioni fornite nelle fonti.

        REGOLE CRITICHE:
        1. USA SOLO informazioni ESPLICITAMENTE presenti nelle fonti
        2. Per ogni specifica tecnica, includi la citazione ESATTA
        3. Se un'informazione non è nelle fonti, scrivi "Non specificato nelle fonti disponibili"
        4. NON fare supposizioni o stime
        5. Mantieni un tono tecnico e professionale

        FORMATO RISPOSTA:
        ## Risposta Diretta
        [Risposta concisa alla domanda]

        ## Specifiche Tecniche
        [Dettagli tecnici con citazioni]

        ## Fonti
        [Lista numerata delle fonti utilizzate]

        DOMANDA: {query}

        FONTI DISPONIBILI:
        {sources}

        RISPOSTA:
        """
    
    def _get_application_template(self) -> str:
        """Template for application and usage responses"""
        return """
        Sei un consulente K-Array per applicazioni audio. Rispondi usando SOLO le informazioni dalle fonti fornite.

        REGOLE CRITICHE:
        1. Raccomanda SOLO prodotti esplicitamente menzionati nelle fonti
        2. Cita esempi di applicazioni SOLO se presenti nelle fonti
        3. Se mancano informazioni, specifica cosa non è disponibile
        4. NON inventare casi d'uso o raccomandazioni

        FORMATO RISPOSTA:
        ## Raccomandazione
        [Risposta diretta con prodotti consigliati]

        ## Applicazioni Documentate
        [Esempi di uso dai case studies]

        ## Considerazioni Tecniche
        [Specifiche rilevanti per l'applicazione]

        ## Fonti
        [Lista delle fonti consultate]

        DOMANDA: {query}

        FONTI DISPONIBILI:
        {sources}

        RISPOSTA:
        """
    
    def _get_comparison_template(self) -> str:
        """Template for product comparison responses"""
        return """
        Sei un tecnico K-Array specializzato in confronti prodotto. Confronta SOLO i prodotti con informazioni disponibili nelle fonti.

        REGOLE CRITICHE:
        1. Confronta SOLO specifiche esplicitamente presenti per entrambi i prodotti
        2. Evidenzia dove mancano dati per il confronto
        3. NON assumere caratteristiche simili se non documentate
        4. Cita fonte per ogni specifica comparata

        FORMATO RISPOSTA:
        ## Confronto Diretto
        [Tabella comparativa delle specifiche disponibili]

        ## Differenze Chiave
        [Principali differenze documentate]

        ## Limitazioni del Confronto
        [Informazioni mancanti per un confronto completo]

        ## Fonti
        [Fonti per ogni prodotto]

        DOMANDA: {query}

        FONTI DISPONIBILI:
        {sources}

        RISPOSTA:
        """
    
    def _get_general_template(self) -> str:
        """Template for general responses"""
        return """
        Sei un assistente K-Array esperto. Rispondi alla domanda usando ESCLUSIVAMENTE le informazioni dalle fonti fornite.

        REGOLE CRITICHE:
        1. Rispondi SOLO con informazioni presenti nelle fonti
        2. Se la risposta non è completa, specifica cosa manca
        3. Includi citazioni per ogni affermazione
        4. Mantieni un tono professionale e utile

        FORMATO RISPOSTA:
        ## Risposta
        [Risposta basata sulle fonti disponibili]

        ## Dettagli Aggiuntivi
        [Informazioni correlate dalle fonti]

        ## Fonti
        [Fonti utilizzate]

        DOMANDA: {query}

        FONTI DISPONIBILI:
        {sources}

        RISPOSTA:
        """
    
    def format_sources(self, results: List[Dict[str, Any]]) -> str:
        """Format retrieval results as sources for LLM"""
        formatted_sources = []
        
        for i, result in enumerate(results, 1):
            metadata = result.get('metadata', {})
            content = result.get('content', '')
            
            source_info = []
            if metadata.get('category'):
                source_info.append(f"Categoria: {metadata['category']}")
            if metadata.get('model'):
                source_info.append(f"Modello: {metadata['model']}")
            if metadata.get('content_type'):
                source_info.append(f"Tipo: {metadata['content_type']}")
            if metadata.get('source_url'):
                source_info.append(f"URL: {metadata['source_url']}")
            
            source_header = f"FONTE {i}: {' | '.join(source_info)}"
            formatted_sources.append(f"{source_header}\n{content}\n")
        
        return "\n---\n".join(formatted_sources)
    
    def validate_response_quality(self, 
                                 response: str, 
                                 sources: List[Dict[str, Any]],
                                 query: str) -> ResponseMetrics:
        """Validate response quality and compute metrics"""
        
        # Basic quality checks
        has_sources_section = "## Fonti" in response or "## Source" in response
        response_length = len(response.strip())
        source_count = len(sources)
        
        # Technical accuracy indicators
        has_specs = any(word in response.lower() for word in ['w', 'hz', 'db', 'mm', 'kg', 'ohm'])
        no_speculation = not any(word in response.lower() for word in 
                               ['probabilmente', 'tipicamente', 'solitamente', 'stimato', 'circa'])
        
        # Completeness indicators
        has_direct_answer = "## Risposta" in response or response_length > 100
        addresses_query = any(word in response.lower() for word in query.lower().split()[:3])
        
        # Calculate scores
        confidence_score = 0.0
        if has_sources_section: confidence_score += 0.3
        if source_count >= 2: confidence_score += 0.2
        if no_speculation: confidence_score += 0.3
        if has_direct_answer: confidence_score += 0.2
        
        technical_accuracy = 0.8 if (has_specs and no_speculation) else 0.6
        completeness = 0.9 if (has_direct_answer and addresses_query) else 0.7
        
        return ResponseMetrics(
            confidence_score=min(1.0, confidence_score),
            source_count=source_count,
            technical_accuracy=technical_accuracy,
            completeness=completeness,
            response_time=0.0,  # Will be set by caller
            llm_provider_used="unknown",
            fallback_triggered=False
        )
    
    def generate_response_with_fallback(self, 
                                      query: str,
                                      sources: List[Dict[str, Any]],
                                      context: RetrievalContext,
                                      conversation_history: Optional[List[Dict[str, str]]] = None) -> Tuple[str, ResponseMetrics]:
        """Generate response with LLM fallback mechanism"""
        
        start_time = datetime.now()
        
        # Format sources
        formatted_sources = self.format_sources(sources)
        
        # Select appropriate template
        template = self.response_templates.get(context.query_type, self.response_templates['general'])
        
        # Prepare prompt
        prompt = template.format(
            query=query,
            sources=formatted_sources
        )
        
        # Add conversation context if available
        if conversation_history:
            context_text = self._format_conversation_context(conversation_history)
            prompt = f"CONTESTO CONVERSAZIONE:\n{context_text}\n\n{prompt}"
        
        # Try primary LLM
        try:
            self.logger.info(f"Attempting response generation with primary LLM: {self.primary_llm.provider}")
            response = self.primary_llm.generate_response(
                prompt=prompt,
                max_tokens=2000,
                temperature=0.1  # Low temperature for factual responses
            )
            
            # Validate response quality
            metrics = self.validate_response_quality(response, sources, query)
            metrics.llm_provider_used = self.primary_llm.provider
            metrics.fallback_triggered = False
            
            # Check if response meets quality thresholds
            if metrics.confidence_score >= self.min_confidence and metrics.source_count >= self.min_sources:
                response_time = (datetime.now() - start_time).total_seconds()
                metrics.response_time = response_time
                
                self.logger.info(f"Primary LLM response successful (confidence: {metrics.confidence_score:.2f})")
                return response, metrics
            else:
                self.logger.warning(f"Primary LLM response quality insufficient (confidence: {metrics.confidence_score:.2f})")
                
        except Exception as e:
            self.logger.error(f"Primary LLM failed: {str(e)}")
        
        # Fallback to secondary LLM
        try:
            self.logger.info(f"Falling back to secondary LLM: {self.fallback_llm.provider}")
            response = self.fallback_llm.generate_response(
                prompt=prompt,
                max_tokens=2000,
                temperature=0.1
            )
            
            # Validate fallback response
            metrics = self.validate_response_quality(response, sources, query)
            metrics.llm_provider_used = self.fallback_llm.provider
            metrics.fallback_triggered = True
            
            response_time = (datetime.now() - start_time).total_seconds()
            metrics.response_time = response_time
            
            self.logger.info(f"Fallback LLM response successful (confidence: {metrics.confidence_score:.2f})")
            return response, metrics
            
        except Exception as e:
            self.logger.error(f"Fallback LLM also failed: {str(e)}")
            
            # Return error response
            error_response = self._generate_error_response(query, sources)
            error_metrics = ResponseMetrics(
                confidence_score=0.0,
                source_count=len(sources),
                technical_accuracy=0.0,
                completeness=0.0,
                response_time=(datetime.now() - start_time).total_seconds(),
                llm_provider_used="error",
                fallback_triggered=True
            )
            
            return error_response, error_metrics
    
    def _format_conversation_context(self, conversation_history: List[Dict[str, str]]) -> str:
        """Format conversation history for context"""
        context_lines = []
        for message in conversation_history[-3:]:  # Last 3 messages
            role = message.get('role', 'unknown')
            content = message.get('content', '')[:200]  # Limit context length
            context_lines.append(f"{role.upper()}: {content}")
        
        return "\n".join(context_lines)
    
    def _generate_error_response(self, query: str, sources: List[Dict[str, Any]]) -> str:
        """Generate error response when LLMs fail"""
        return f"""
## Risposta

Mi dispiace, sto riscontrando difficoltà tecniche nella generazione della risposta per la tua domanda: "{query}"

## Fonti Disponibili

Ho trovato {len(sources)} fonti rilevanti nei miei database K-Array, ma non riesco a processarle correttamente al momento.

## Suggerimento

Ti consiglio di riprovare con una domanda più specifica o di contattare il supporto tecnico K-Array per assistenza diretta.

## Fonti
{len(sources)} documenti K-Array identificati ma non processabili
        """
    
    def enhance_response_with_metadata(self, 
                                     response: str, 
                                     metrics: ResponseMetrics,
                                     context: RetrievalContext) -> str:
        """Enhance response with metadata for debugging/transparency"""
        
        if metrics.confidence_score < 0.8:
            confidence_notice = "\n\n*Nota: Questa risposta ha una confidenza limitata. Verifica sempre con la documentazione ufficiale K-Array.*"
            response += confidence_notice
        
        if metrics.fallback_triggered:
            fallback_notice = f"\n\n*Sistema: Risposta generata con LLM di backup ({metrics.llm_provider_used})*"
            response += fallback_notice
        
        return response


if __name__ == "__main__":
    # Test the response engine
    from src.enhanced_vector_store import EnhancedVectorStore
    from src.smart_retriever import SmartRetriever
    
    # Initialize components
    vector_store = EnhancedVectorStore()
    retriever = SmartRetriever(vector_store)
    response_engine = ResponseEngine()
    
    # Test query
    query = "What are the power specifications of the Kommander amplifiers?"
    
    # Get results and context
    results, context = retriever.search(query)
    
    # Generate response
    response, metrics = response_engine.generate_response_with_fallback(
        query=query,
        sources=results,
        context=context
    )
    
    print(f"Query: {query}")
    print(f"Response confidence: {metrics.confidence_score:.2f}")
    print(f"LLM used: {metrics.llm_provider_used}")
    print(f"Response:\n{response}")