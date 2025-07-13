import google.generativeai as genai
import openai
from typing import Optional, Dict, Any
import logging
from src.config import Config

class LLMManager:
    """Manager for LLM providers (Gemini and OpenAI)"""
    
    def __init__(self, provider: str = None):
        self.provider = provider or Config.DEFAULT_LLM_PROVIDER
        self.setup_logging()
        self.initialize_clients()
    
    def setup_logging(self):
        """Setup logging"""
        self.logger = logging.getLogger(__name__)
    
    def initialize_clients(self):
        """Initialize LLM clients"""
        try:
            if self.provider == "gemini":
                if not Config.GEMINI_API_KEY:
                    raise ValueError("GEMINI_API_KEY not found in environment variables")
                genai.configure(api_key=Config.GEMINI_API_KEY)
                self.logger.info(f"Gemini API key configured: {Config.GEMINI_API_KEY[:8]}***")
                self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
                self.logger.info("Gemini client initialized")
            
            elif self.provider == "openai":
                if not Config.OPENAI_API_KEY:
                    raise ValueError("OPENAI_API_KEY not found in environment variables")
                self.openai_client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
                self.logger.info("OpenAI client initialized")
            
            else:
                raise ValueError(f"Unsupported LLM provider: {self.provider}")
                
        except Exception as e:
            self.logger.error(f"Error initializing LLM client: {str(e)}")
            raise
    
    def generate_response(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> str:
        """Generate response from LLM"""
        try:
            if self.provider == "gemini":
                return self._generate_gemini_response(prompt, max_tokens, temperature)
            elif self.provider == "openai":
                return self._generate_openai_response(prompt, max_tokens, temperature)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
                
        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            return f"Error: Unable to generate response. {str(e)}"
    
    def generate_text(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> str:
        """Generate text from LLM (alias for generate_response for compatibility)"""
        return self.generate_response(prompt, max_tokens, temperature)
    
    def _generate_gemini_response(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Generate response using Gemini"""
        try:
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature
            )
            
            response = self.gemini_model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            return response.text
            
        except Exception as e:
            self.logger.error(f"Error with Gemini API: {str(e)}")
            raise
    
    def _generate_openai_response(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Generate response using OpenAI"""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            self.logger.error(f"Error with OpenAI API: {str(e)}")
            raise
    
    def extract_structured_data(self, text: str, data_type: str = "general") -> str:
        """Extract structured data from text using LLM"""
        try:
            if data_type == "csv":
                prompt = f"""
                Analyze the following CSV data and extract key information in a structured format.
                Focus on identifying:
                1. Column headers and their meanings
                2. Data types and patterns
                3. Key relationships between columns
                4. Summary statistics where relevant
                5. Any notable patterns or anomalies

                CSV Data:
                {text}

                Provide a clear, structured summary that would be useful for a RAG system.
                """
            
            elif data_type == "pdf":
                prompt = f"""
                Analyze the following PDF text content and extract key information in a structured format.
                Focus on identifying:
                1. Main topics and themes
                2. Key facts and figures
                3. Important concepts and definitions
                4. Relationships between different sections
                5. Action items or conclusions

                PDF Content:
                {text}

                Provide a clear, structured summary that would be useful for a RAG system.
                """
            
            else:
                prompt = f"""
                Analyze the following text and extract key information in a structured format.
                Focus on identifying:
                1. Main topics and themes
                2. Key facts and figures
                3. Important concepts and definitions
                4. Relationships between different sections

                Text Content:
                {text}

                Provide a clear, structured summary that would be useful for a RAG system.
                """
            
            return self.generate_response(prompt, max_tokens=2000, temperature=0.3)
            
        except Exception as e:
            self.logger.error(f"Error extracting structured data: {str(e)}")
            return f"Error extracting data: {str(e)}"
    
    def generate_rag_response(self, query: str, context: str, sources: list = None) -> Dict[str, Any]:
        """Generate RAG response with context"""
        try:
            # Prepare sources information
            sources_text = ""
            if sources:
                sources_text = "\n\nSources:\n" + "\n".join([
                    f"- {source.get('title', 'Unknown')} ({source.get('url', 'No URL')})" 
                    for source in sources
                ])
            
            prompt = f"""
            You are an AI assistant that answers questions based on provided context.
            
            Context:
            {context}
            
            Question: {query}
            
            Instructions:
            1. Answer the question based only on the provided context
            2. Be specific and accurate
            3. If the context doesn't contain enough information to answer the question, say so
            4. Provide a clear, well-structured response
            5. Reference specific information from the context when relevant
            
            Answer:
            """
            
            response = self.generate_response(prompt, max_tokens=1500, temperature=0.5)
            
            # Add sources to response
            if sources:
                response += sources_text
            
            return {
                "response": response,
                "sources": sources or [],
                "context_used": context
            }
            
        except Exception as e:
            self.logger.error(f"Error generating RAG response: {str(e)}")
            return {
                "response": f"Error generating response: {str(e)}",
                "sources": [],
                "context_used": ""
            }
    
    def switch_provider(self, new_provider: str):
        """Switch LLM provider"""
        try:
            if new_provider not in ["gemini", "openai"]:
                raise ValueError(f"Unsupported provider: {new_provider}")
            
            self.provider = new_provider
            self.initialize_clients()
            self.logger.info(f"Switched to {new_provider} provider")
            
        except Exception as e:
            self.logger.error(f"Error switching provider: {str(e)}")
            raise
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get current provider information"""
        return {
            "current_provider": self.provider,
            "available_providers": ["gemini", "openai"],
            "gemini_available": bool(Config.GEMINI_API_KEY),
            "openai_available": bool(Config.OPENAI_API_KEY)
        }