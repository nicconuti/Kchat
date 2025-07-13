#!/usr/bin/env python3
"""
K-Array Expert Chat System
Gradio interface with session memory, vector retrieval, and zero-hallucination responses
"""

import gradio as gr
import logging
from typing import List, Dict, Tuple
from datetime import datetime
import time

# Import our custom components
from src.local_vector_store import LocalVectorStore
from src.smart_retriever import SmartRetriever
from src.multi_vector_retriever import MultiVectorRetriever
from src.response_engine import ResponseEngine
from src.config import Config
from src.dynamic_config import dynamic_config
from src.llm_manager import LLMManager

# Try to import LangGraph system
try:
    from src.langgraph_k_array_rag import KArrayAgenticRAG, LANGGRAPH_AVAILABLE
    USE_LANGGRAPH = True
except ImportError:
    USE_LANGGRAPH = False
    LANGGRAPH_AVAILABLE = False


class KArrayChatSystem:
    """Main chat system integrating all components"""
    
    def __init__(self):
        self.setup_logging()
        self.initialize_components()
        self.session_store = {}  # Store conversation sessions
        
    def setup_logging(self):
        """Setup logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('data/chat_system.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def initialize_components(self):
        """Initialize all system components"""
        try:
            self.logger.info("Initializing K-Array Chat System...")
            
            # Initialize vector store
            self.logger.info("Loading vector store...")
            self.vector_store = LocalVectorStore()
            
            # Check if data needs to be ingested
            stats = self.vector_store.get_stats()
            if stats['total_documents'] == 0:
                self.logger.info("Vector store is empty, ingesting JSON files...")
                ingested_count = self.vector_store.ingest_json_files()
                self.logger.info(f"Ingested {ingested_count} documents")
            else:
                self.logger.info(f"Vector store ready with {stats['total_documents']} documents")
            
            # Initialize retriever with multi-vector capabilities
            self.logger.info("Initializing advanced multi-vector retriever...")
            self.retriever = MultiVectorRetriever(
                self.vector_store, 
                enable_reranking=True, 
                enable_fusion=True
            )
            
            # Also initialize smart retriever as fallback
            self.logger.info("Initializing smart retriever as fallback...")
            self.fallback_retriever = SmartRetriever(self.vector_store, enable_reranking=True)
            
            # Initialize response engine
            self.logger.info("Initializing response engine...")
            self.response_engine = ResponseEngine()
            
            self.logger.info("K-Array Chat System initialized successfully!")
            
        except Exception as e:
            self.logger.error(f"Error initializing chat system: {str(e)}")
            raise
    
    def get_session_id(self, request: gr.Request) -> str:
        """Generate or retrieve session ID"""
        if hasattr(request, 'session_hash'):
            return request.session_hash
        return f"session_{int(time.time())}"
    
    def get_conversation_history(self, session_id: str) -> List[Dict[str, str]]:
        """Get conversation history for session"""
        return self.session_store.get(session_id, {}).get('history', [])
    
    def update_conversation_history(self, session_id: str, role: str, content: str):
        """Update conversation history"""
        if session_id not in self.session_store:
            self.session_store[session_id] = {'history': [], 'metadata': {}}
        
        self.session_store[session_id]['history'].append({
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep only last 10 messages to manage memory
        if len(self.session_store[session_id]['history']) > 10:
            self.session_store[session_id]['history'] = self.session_store[session_id]['history'][-10:]
    
    def process_query(self, 
                     message: str, 
                     history: List[List[str]], 
                     request: gr.Request) -> Tuple[str, List[List[str]]]:
        """Process user query and return response"""
        
        if not message or not message.strip():
            return "", history
        
        try:
            # Get session ID
            session_id = self.get_session_id(request)
            
            # Get conversation context
            conversation_history = self.get_conversation_history(session_id)
            
            # Update history with user message
            self.update_conversation_history(session_id, 'user', message)
            
            self.logger.info(f"Processing query from session {session_id}: {message[:100]}...")
            
            # Retrieve relevant documents using multi-vector retrieval with intelligence
            try:
                results, query_intelligence = self.retriever.retrieve(
                    query=message,
                    max_results=5,
                    conversation_history=conversation_history
                )
                
                self.logger.info(f"Multi-vector retrieval: {len(results)} documents")
                
                # Check if clarification is needed
                if (query_intelligence and 
                    hasattr(self.retriever, 'query_intelligence') and 
                    self.retriever.query_intelligence and
                    self.retriever.query_intelligence.should_ask_clarification(query_intelligence)):
                    
                    # Generate clarification question instead of proceeding
                    clarification = self.retriever.query_intelligence.generate_clarification_question(query_intelligence)
                    
                    self.logger.info(f"Requesting clarification: {clarification}")
                    
                    # Create clarification response
                    clarification_response = f"""
                    Ho bisogno di più dettagli per fornirti la risposta più precisa possibile.
                    
                    {clarification}
                    
                    📝 *Questo mi aiuterà a trovare esattamente le informazioni che cerchi nel database K-Array.*
                    """
                    
                    # Update history
                    self.update_conversation_history(session_id, 'assistant', clarification_response)
                    history.append([message, clarification_response])
                    
                    return "", history
                
                # Create enhanced context from query intelligence
                if query_intelligence:
                    context = type('Context', (), {
                        'original_query': message,
                        'processed_query': query_intelligence.optimized_query,
                        'query_type': query_intelligence.intent.value,
                        'detected_products': query_intelligence.products_mentioned,
                        'detected_categories': query_intelligence.application_focus,
                        'intent': query_intelligence.intent.value,
                        'confidence': query_intelligence.confidence,
                        'language': query_intelligence.language,
                        'query_intelligence': query_intelligence
                    })()
                else:
                    # Fallback context
                    context = type('Context', (), {
                        'original_query': message,
                        'processed_query': message,
                        'query_type': 'general',
                        'detected_products': [],
                        'detected_categories': [],
                        'intent': 'general',
                        'confidence': 0.8
                    })()
                
            except Exception as e:
                self.logger.warning(f"Multi-vector retrieval failed, using fallback: {str(e)}")
                # Fallback to smart retriever
                results, context = self.fallback_retriever.search(
                    query=message,
                    conversation_history=conversation_history,
                    max_results=5
                )
                self.logger.info(f"Fallback retrieval: {len(results)} documents")
            
            # Generate response
            response, metrics = self.response_engine.generate_response_with_fallback(
                query=message,
                sources=results,
                context=context,
                conversation_history=conversation_history
            )
            
            # Enhance response with metadata if needed
            enhanced_response = self.response_engine.enhance_response_with_metadata(
                response, metrics, context
            )
            
            # Update history with assistant response
            self.update_conversation_history(session_id, 'assistant', enhanced_response)
            
            # Update Gradio chat history
            history.append([message, enhanced_response])
            
            # Log metrics
            self.logger.info(f"Response generated - Confidence: {metrics.confidence_score:.2f}, "
                           f"LLM: {metrics.llm_provider_used}, Time: {metrics.response_time:.2f}s")
            
            return "", history
            
        except Exception as e:
            self.logger.error(f"Error processing query: {str(e)}")
            error_response = f"Mi dispiace, ho riscontrato un errore nel processare la tua richiesta: {str(e)}"
            history.append([message, error_response])
            return "", history
    
    def clear_conversation(self, request: gr.Request) -> List[List[str]]:
        """Clear conversation history"""
        session_id = self.get_session_id(request)
        if session_id in self.session_store:
            self.session_store[session_id]['history'] = []
        self.logger.info(f"Cleared conversation for session {session_id}")
        return []
    
    def get_system_stats(self) -> str:
        """Get system statistics"""
        try:
            stats = self.vector_store.get_stats()
            return f"""
**Sistema K-Array Chat Avanzato**
- Documenti nel database: {stats['total_documents']}
- Vector Store: Milvus (35k+ stars)
- Retrieval: Multi-Vector + Cross-Encoder Reranking
- Strategie attive: 6 (Fusion + RRF)
- Ultimo aggiornamento: {stats.get('last_updated', 'N/A')}
- Sessioni attive: {len(self.session_store)}
- Provider LLM: Gemini (primario) + OpenAI (fallback)
- Qualità: Zero-hallucination + Source Attribution
            """
        except Exception as e:
            return f"Errore nel recupero statistiche: {str(e)}"
    
    def create_interface(self) -> gr.Blocks:
        """Create Gradio interface"""
        
        # Custom CSS for better styling
        custom_css = """
        .chat-container {
            max-height: 600px;
            overflow-y: auto;
        }
        .system-info {
            background-color: #f0f0f0;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
        }
        .warning-text {
            color: #ff6b6b;
            font-style: italic;
        }
        """
        
        with gr.Blocks(css=custom_css, title="K-Array Expert Chat") as interface:
            
            # Header
            gr.Markdown("""
            # 🎵 K-Array Expert Chat System
            
            Sistema di chat avanzato per informazioni tecniche sui prodotti K-Array.
            Utilizza intelligenza artificiale con **zero allucinazioni** e citazioni delle fonti.
            """)
            
            # Main chat interface
            with gr.Row():
                with gr.Column(scale=4):
                    chatbot = gr.Chatbot(
                        label="Chat con l'Esperto K-Array",
                        height=500,
                        elem_classes=["chat-container"]
                    )
                    
                    with gr.Row():
                        msg = gr.Textbox(
                            label="La tua domanda",
                            placeholder="Esempio: Quali sono le specifiche di potenza del Kommander KA104?",
                            lines=2,
                            scale=4
                        )
                        send_btn = gr.Button("Invia", variant="primary", scale=1)
                    
                    with gr.Row():
                        clear_btn = gr.Button("Nuova Conversazione", variant="secondary")
                
                with gr.Column(scale=1):
                    # System information panel
                    gr.Markdown("## 📊 Info Sistema")
                    
                    stats_display = gr.Markdown(
                        self.get_system_stats(),
                        elem_classes=["system-info"]
                    )
                    
                    refresh_stats_btn = gr.Button("Aggiorna Stats", size="sm")
                    
                    # Usage tips
                    gr.Markdown("""
                    ## 💡 Suggerimenti
                    
                    **Esempi di domande:**
                    - Specifiche tecniche del KA104
                    - Applicazioni per hotel e ristoranti
                    - Confronto tra Lyzard e Vyper
                    - Installazione per teatri
                    
                    **Caratteristiche:**
                    ✅ Zero allucinazioni  
                    ✅ Citazioni fonti  
                    ✅ Memoria conversazione  
                    ✅ Fallback LLM  
                    """)
            
            # Warning notice
            gr.Markdown("""
            ---
            **⚠️ Avviso:** Questo sistema fornisce informazioni basate sui dati disponibili. 
            Per decisioni critiche, consulta sempre la documentazione ufficiale K-Array.
            """, elem_classes=["warning-text"])
            
            # Event handlers
            def submit_message(message, history, request):
                return self.process_query(message, history, request)
            
            def clear_chat(request):
                return self.clear_conversation(request)
            
            def refresh_stats():
                return self.get_system_stats()
            
            # Bind events
            msg.submit(submit_message, [msg, chatbot], [msg, chatbot])
            send_btn.click(submit_message, [msg, chatbot], [msg, chatbot])
            clear_btn.click(clear_chat, None, chatbot)
            refresh_stats_btn.click(refresh_stats, None, stats_display)
            
            # Example queries for quick testing
            gr.Examples(
                examples=[
                    ["Quali sono le specifiche del Kommander KA104?"],
                    ["Prodotti consigliati per installazioni in hotel"],
                    ["Differenze tra serie Lyzard e Vyper"],
                    ["Come installare sistemi per teatri?"],
                    ["Specifiche di potenza amplificatori"],
                    ["Applicazioni per fitness e wellness"]
                ],
                inputs=msg,
                label="Esempi di domande"
            )
        
        return interface


def main():
    """Main function to launch the chat system"""
    
    # Validate configuration
    try:
        Config.validate_config()
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("Please set the required API keys in your .env file or environment variables.")
        return
    
    # Initialize chat system
    try:
        chat_system = KArrayChatSystem()
        
        # Create and launch interface
        interface = chat_system.create_interface()
        
        print("🚀 Launching K-Array Expert Chat System...")
        print("📋 Make sure your API keys are configured in .env file")
        print("🔗 The interface will be available at: http://localhost:7860")
        
        # Get server configuration from dynamic config
        server_config = dynamic_config.server_config
        
        interface.launch(
            server_name=server_config.host,
            server_port=server_config.port,
            share=server_config.share,
            debug=server_config.debug,
            show_error=True
        )
        
    except Exception as e:
        print(f"❌ Error launching chat system: {e}")
        logging.error(f"Launch error: {e}")


if __name__ == "__main__":
    main()