#!/usr/bin/env python3
"""
K-Array Expert Chat System V2
Modern Gradio interface with LangGraph Agentic RAG and intelligent orchestration
"""

import gradio as gr
import logging
import time
from typing import List, Dict, Tuple, Optional
from datetime import datetime

from src.local_vector_store import LocalVectorStore
from src.llm_manager import LLMManager

# Try to import LangGraph system
try:
    from src.langgraph_k_array_rag import KArrayAgenticRAG, LANGGRAPH_AVAILABLE
    if LANGGRAPH_AVAILABLE:
        USE_AGENTIC_RAG = True
    else:
        USE_AGENTIC_RAG = False
        print("⚠️ LangGraph dependencies missing")
except ImportError:
    USE_AGENTIC_RAG = False
    print("⚠️ LangGraph system not available")

# Fallback imports for basic RAG
if not USE_AGENTIC_RAG:
    from src.smart_retriever import SmartRetriever
    from src.response_engine import ResponseEngine


class ModernKArrayChat:
    """Modern K-Array chat system with LangGraph Agentic RAG"""
    
    def __init__(self):
        self.setup_logging()
        self.session_store = {}
        self.initialize_system()
        
    def setup_logging(self):
        """Setup logging system with Windows-compatible encoding"""
        import sys
        
        # Create handlers with proper encoding
        file_handler = logging.FileHandler('data/chat_system.log', encoding='utf-8')
        
        # For console, use utf-8 or fallback to safe encoding
        try:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setStream(sys.stdout)
        except:
            console_handler = logging.StreamHandler()
        
        # Set formatters
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            handlers=[file_handler, console_handler],
            force=True
        )
        self.logger = logging.getLogger(__name__)
    
    def initialize_system(self):
        """Initialize the complete chat system"""
        try:
            self.logger.info("Initializing Modern K-Array Chat System...")
            
            # Initialize vector store
            self.logger.info("Loading vector store...")
            self.vector_store = LocalVectorStore()
            
            # Auto-ingest data if needed
            stats = self.vector_store.get_stats()
            if stats['total_documents'] == 0:
                self.logger.info("Vector store empty - ingesting data...")
                ingested_count = self.vector_store.ingest_json_files()
                self.logger.info(f"Ingested {ingested_count} documents")
            else:
                self.logger.info(f"Vector store ready with {stats['total_documents']} documents")
            
            # Initialize LLM manager
            self.logger.info("Initializing LLM manager...")
            self.llm_manager = LLMManager()
            
            # Initialize RAG system
            if USE_AGENTIC_RAG:
                self.logger.info("Initializing LangGraph Agentic RAG system...")
                self.rag_system = KArrayAgenticRAG(self.vector_store, self.llm_manager)
                self.system_type = "LangGraph Agentic RAG"
                self.logger.info("LangGraph Agentic RAG system ready!")
            else:
                self.logger.info("Initializing fallback RAG system...")
                self.retriever = SmartRetriever(self.vector_store, enable_reranking=True)
                self.response_engine = ResponseEngine()
                self.system_type = "Traditional RAG"
                self.logger.info("Traditional RAG system ready!")
            
            self.logger.info(f"System initialized with: {self.system_type}")
            
        except Exception as e:
            self.logger.error(f"Error initializing system: {str(e)}")
            raise
    
    def process_query(self, user_query: str, session_id: str) -> str:
        """Process user query with the active RAG system"""
        try:
            self.logger.info(f"Processing query: {user_query}")
            start_time = time.time()
            
            # Update conversation history
            self.update_conversation_history(session_id, "user", user_query)
            
            if USE_AGENTIC_RAG:
                # Use LangGraph Agentic RAG
                response = self.rag_system.process_query(user_query)
            else:
                # Use traditional RAG fallback
                response = self.process_with_traditional_rag(user_query, session_id)
            
            # Update conversation history with response
            self.update_conversation_history(session_id, "assistant", response)
            
            # Log performance
            processing_time = time.time() - start_time
            self.logger.info(f"Query processed in {processing_time:.2f}s using {self.system_type}")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error processing query: {str(e)}")
            return "Mi dispiace, ho riscontrato un errore nell'elaborazione della tua domanda. Puoi riprovare riformulando la domanda?"
    
    def process_with_traditional_rag(self, user_query: str, session_id: str) -> str:
        """Fallback processing with traditional RAG"""
        try:
            # Get conversation context
            history = self.get_conversation_history(session_id)
            
            # Retrieve relevant documents
            context = self.retriever.retrieve_with_context(
                query=user_query,
                conversation_history=history[-5:] if history else [],  # Last 5 exchanges
                top_k=10
            )
            
            # Generate response
            response = self.response_engine.generate_response(
                query=user_query,
                context=context,
                conversation_history=history[-3:] if history else []  # Last 3 exchanges
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error in traditional RAG: {str(e)}")
            return "Mi dispiace, ho riscontrato un errore. Puoi riprovare?"
    
    def get_conversation_history(self, session_id: str) -> List[Dict[str, str]]:
        """Get conversation history for session"""
        return self.session_store.get(session_id, {}).get('history', [])
    
    def update_conversation_history(self, session_id: str, role: str, content: str):
        """Update conversation history"""
        if session_id not in self.session_store:
            self.session_store[session_id] = {
                'history': [],
                'created_at': datetime.now().isoformat(),
                'system_type': self.system_type
            }
        
        self.session_store[session_id]['history'].append({
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep only last 20 exchanges to prevent memory bloat
        if len(self.session_store[session_id]['history']) > 40:  # 20 exchanges = 40 messages
            self.session_store[session_id]['history'] = self.session_store[session_id]['history'][-40:]
    
    def get_session_id(self, request: gr.Request) -> str:
        """Generate or retrieve session ID"""
        if hasattr(request, 'session_hash'):
            return request.session_hash
        return f"session_{int(time.time())}"
    
    def chat_interface(self, message: str, history: List[Dict], request: gr.Request) -> Tuple[str, List[Dict]]:
        """Main chat interface function"""
        try:
            # Get session ID
            session_id = self.get_session_id(request)
            
            # Process the query
            response = self.process_query(message, session_id)
            
            # Update Gradio history with new messages format
            if history is None:
                history = []
            
            # Add user message
            history.append({"role": "user", "content": message})
            # Add assistant response
            history.append({"role": "assistant", "content": response})
            
            return "", history
            
        except Exception as e:
            self.logger.error(f"Error in chat interface: {str(e)}")
            error_response = "Mi dispiace, si è verificato un errore. Riprova per favore."
            
            if history is None:
                history = []
            
            # Add user message and error response
            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": error_response})
            
            return "", history
    
    def get_system_info(self) -> str:
        """Get system information for display"""
        stats = self.vector_store.get_stats()
        
        info = f"""
        ## 🤖 K-Array Expert Chat System
        
        **Sistema attivo:** {self.system_type}
        **Documenti nel database:** {stats['total_documents']:,}
        **Ultimo aggiornamento:** {stats.get('last_updated', 'N/A')}
        
        ### 🎯 Capabilities
        """
        
        if USE_AGENTIC_RAG:
            info += """
        - ✅ **Agentic RAG** con LangGraph
        - ✅ **Multi-stage retrieval** intelligente
        - ✅ **Fuzzy product matching** avanzato
        - ✅ **Iterative refinement** automatico
        - ✅ **Context-aware search** strategies
        """
        else:
            info += """
        - ✅ **Smart retrieval** con reranking
        - ✅ **Multi-vector search** 
        - ✅ **Conversation context**
        - ✅ **Source attribution**
        """
        
        info += """
        
        ### 💡 Esempi di domande
        - "Specifiche tecniche del Kommander KA104"
        - "Differenze tra serie Lyzard e Vyper"
        - "Applicazioni per il Firenze KH7"
        - "Software K-Framework caratteristiche"
        """
        
        return info
    
    def create_interface(self) -> gr.Blocks:
        """Create the Gradio interface"""
        
        with gr.Blocks(
            title="K-Array Expert Chat",
            theme=gr.themes.Soft(primary_hue="blue"),
            css="""
            .gradio-container {
                max-width: 1200px !important;
                margin: auto !important;
            }
            .chat-container {
                height: 600px !important;
            }
            """
        ) as interface:
            
            gr.Markdown("# 🎵 K-Array Expert Chat System")
            gr.Markdown("*Sistema di chat intelligente per prodotti K-Array con tecnologia avanzata*")
            
            with gr.Row():
                with gr.Column(scale=3):
                    # Main chat interface
                    chatbot = gr.Chatbot(
                        value=[],
                        height=500,
                        label="💬 Chat con l'esperto K-Array",
                        show_copy_button=True,
                        container=True,
                        type="messages"
                    )
                    
                    with gr.Row():
                        msg = gr.Textbox(
                            placeholder="Chiedi informazioni sui prodotti K-Array...",
                            label="La tua domanda",
                            lines=2,
                            max_lines=5,
                            scale=4
                        )
                        send_btn = gr.Button("Invia", variant="primary", scale=1)
                    
                    # Examples
                    with gr.Row():
                        gr.Examples(
                            examples=[
                                "Specifiche del Kommander KA208",
                                "Differenze tra Lyzard KZ1I e Vyper KV25I", 
                                "Applicazioni del Firenze KS8",
                                "Informazioni sul K-Framework",
                                "Serie Mugello caratteristiche"
                            ],
                            inputs=msg,
                            label="💡 Esempi di domande"
                        )
                
                with gr.Column(scale=1):
                    # System info panel
                    system_info = gr.Markdown(
                        value=self.get_system_info(),
                        label="ℹ️ Informazioni Sistema"
                    )
                    
                    # Clear chat button
                    clear_btn = gr.Button("🗑️ Cancella Chat", variant="secondary")
            
            # Event handlers
            def handle_message(message, history, request):
                return self.chat_interface(message, history, request)
            
            def clear_chat():
                return [], ""
            
            # Bind events
            msg.submit(handle_message, [msg, chatbot], [msg, chatbot])
            send_btn.click(handle_message, [msg, chatbot], [msg, chatbot])
            clear_btn.click(clear_chat, [], [chatbot, msg])
            
            # Footer
            gr.Markdown(
                f"""
                ---
                *Powered by {self.system_type} • 
                K-Array Product Database • 
                Built with ❤️ for audio professionals*
                """,
                elem_classes="footer"
            )
        
        return interface
    
    def launch(self, **kwargs):
        """Launch the chat system"""
        try:
            self.logger.info("Launching K-Array Chat System...")
            
            interface = self.create_interface()
            
            default_kwargs = {
                'server_name': '0.0.0.0',
                'server_port': 7860,
                'show_api': False,
                'share': False
            }
            default_kwargs.update(kwargs)
            
            self.logger.info(f"Starting server on http://localhost:{default_kwargs['server_port']}")
            
            interface.launch(**default_kwargs)
            
        except Exception as e:
            self.logger.error(f"Error launching chat system: {str(e)}")
            raise


def main():
    """Main function"""
    try:
        print("🎵 K-Array Expert Chat System V2")
        print("=" * 50)
        
        # System information
        if USE_AGENTIC_RAG:
            print("🤖 Using: LangGraph Agentic RAG")
            print("✨ Features: Multi-stage retrieval, intelligent orchestration")
        else:
            print("📖 Using: Traditional RAG (LangGraph not available)")
            print("💡 To enable Agentic RAG: pip install langgraph langchain langchain-core")
        
        print()
        
        # Initialize and launch
        chat_system = ModernKArrayChat()
        chat_system.launch()
        
    except KeyboardInterrupt:
        print("\n👋 Chat system stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        logging.error(f"Launch error: {e}")


if __name__ == "__main__":
    main()