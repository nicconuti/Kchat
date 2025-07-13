#!/usr/bin/env python3
"""
K-Array Agentic RAG System using LangGraph
Advanced multi-stage retrieval with intelligent orchestration for K-Array products
"""

import json
import logging
import re
import difflib
from typing import List, Dict, Any, Optional, Tuple, TypedDict, Annotated
from dataclasses import dataclass

# LangGraph imports
try:
    from langgraph.graph import StateGraph, END
    from langgraph.graph.message import MessagesState
    from langgraph.prebuilt import ToolNode
    from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
    from langchain_core.tools import tool
    from langchain_core.runnables import RunnableLambda
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    print("⚠️ LangGraph not available. Install with: pip install langgraph langchain")

from src.local_vector_store import LocalVectorStore
from src.llm_manager import LLMManager


class KArrayRAGState(TypedDict):
    """State for K-Array RAG workflow"""
    messages: Annotated[List[BaseMessage], "Conversation messages"]
    original_query: str
    processed_query: str
    detected_products: List[str]
    search_results: List[Dict[str, Any]]
    evaluation_result: Optional[Dict[str, Any]]
    needs_refinement: bool
    iteration_count: int
    final_answer: Optional[str]


class KArrayProductMatcher:
    """Advanced product matching with fuzzy search for K-Array products"""
    
    def __init__(self):
        self.product_knowledge = {
            'products': {
                # Kommander Series - Amplifiers & Controllers
                'ka104': {
                    'aliases': ['ka104', 'kommander ka104', 'kommander-ka104', 'ka-104'],
                    'series': 'kommander',
                    'type': 'amplifier',
                    'keywords': ['amplifier', '4 channel', 'class d']
                },
                'ka104live': {
                    'aliases': ['ka104live', 'ka104-live', 'kommander ka104live'],
                    'series': 'kommander',
                    'type': 'amplifier',
                    'keywords': ['amplifier', '4 channel', 'live', 'class d']
                },
                'ka208': {
                    'aliases': ['ka208', 'kommander ka208', 'kommander-ka208', 'ka-208'],
                    'series': 'kommander',
                    'type': 'amplifier',
                    'keywords': ['amplifier', '8 channel', 'class d']
                },
                'ka02i': {
                    'aliases': ['ka02i', 'ka02-i', 'kommander ka02i', 'ka-02i'],
                    'series': 'kommander',
                    'type': 'controller',
                    'keywords': ['controller', 'dsp', 'processor']
                },
                
                # Software/Framework
                'k-framework': {
                    'aliases': ['k framework', 'k-framework', 'k framework 3', 'kframework', 'k framework3'],
                    'series': 'software',
                    'type': 'software',
                    'keywords': ['software', 'framework', 'control', 'dsp', 'management']
                },
                
                # Lyzard Series - Line Arrays
                'kz1i': {
                    'aliases': ['kz1i', 'kz1-i', 'lyzard kz1i', 'lyzard-kz1i', 'kz-1i'],
                    'series': 'lyzard',
                    'type': 'line_array',
                    'keywords': ['line array', 'speaker', 'compact', 'passive']
                },
                'kz14i': {
                    'aliases': ['kz14i', 'kz14-i', 'lyzard kz14i', 'kz-14i'],
                    'series': 'lyzard',
                    'type': 'line_array',
                    'keywords': ['line array', 'speaker', 'medium', 'passive']
                },
                
                # Vyper Series - High Power Line Arrays
                'kv25i': {
                    'aliases': ['kv25i', 'kv25-i', 'vyper kv25i', 'kv-25i'],
                    'series': 'vyper',
                    'type': 'line_array',
                    'keywords': ['line array', 'speaker', 'high power', 'active']
                },
                
                # Firenze Series
                'kh7': {
                    'aliases': ['kh7', 'firenze kh7', 'firenze-kh7', 'kh-7'],
                    'series': 'firenze',
                    'type': 'line_array',
                    'keywords': ['line array', 'digitally steerable', 'slim', 'discontinued']
                },
                'ks8': {
                    'aliases': ['ks8', 'firenze ks8', 'firenze-ks8', 'ks-8'],
                    'series': 'firenze',
                    'type': 'subwoofer',
                    'keywords': ['subwoofer', 'active', 'ipal', 'weather resistant']
                },
                
                # Mugello Series
                'kh2': {
                    'aliases': ['kh2', 'mugello kh2', 'mugello-kh2', 'kh-2'],
                    'series': 'mugello',
                    'type': 'line_array',
                    'keywords': ['line array', 'small format', 'discontinued']
                },
                'kh3': {
                    'aliases': ['kh3', 'mugello kh3', 'mugello-kh3', 'kh-3'],
                    'series': 'mugello',
                    'type': 'line_array',
                    'keywords': ['line array', 'medium format', 'discontinued']
                }
            },
            'series_info': {
                'kommander': {
                    'description': 'Professional amplifiers and controllers',
                    'keywords': ['amplifier', 'controller', 'dsp', 'professional']
                },
                'lyzard': {
                    'description': 'Compact line array speakers',
                    'keywords': ['line array', 'compact', 'speaker', 'passive']
                },
                'vyper': {
                    'description': 'High-power line array speakers',
                    'keywords': ['line array', 'high power', 'speaker', 'active']
                },
                'firenze': {
                    'description': 'Digitally steerable line arrays and subwoofers',
                    'keywords': ['digitally steerable', 'line array', 'subwoofer']
                },
                'mugello': {
                    'description': 'Mid-high line array elements (discontinued)',
                    'keywords': ['line array', 'mid-high', 'discontinued']
                },
                'software': {
                    'description': 'Software tools and frameworks',
                    'keywords': ['software', 'framework', 'control', 'management']
                }
            }
        }
    
    def fuzzy_match_products(self, query: str, threshold: float = 0.6) -> List[Tuple[str, float, Dict]]:
        """Advanced fuzzy matching with context"""
        matches = []
        query_lower = query.lower()
        
        for product_id, product_data in self.product_knowledge['products'].items():
            best_score = 0.0
            match_type = ""
            
            # Check exact aliases first (highest priority)
            for alias in product_data['aliases']:
                if alias.lower() in query_lower:
                    matches.append((product_id, 1.0, {
                        'match_type': 'exact_alias',
                        'matched_text': alias,
                        'product_data': product_data
                    }))
                    best_score = 1.0
                    break
            
            if best_score < 1.0:
                # Fuzzy matching against aliases
                for alias in product_data['aliases']:
                    similarity = difflib.SequenceMatcher(None, query_lower, alias.lower()).ratio()
                    if similarity >= threshold and similarity > best_score:
                        best_score = similarity
                        match_type = 'fuzzy_alias'
                        matches.append((product_id, similarity, {
                            'match_type': match_type,
                            'matched_text': alias,
                            'product_data': product_data
                        }))
                
                # Check keywords
                for keyword in product_data['keywords']:
                    if keyword.lower() in query_lower:
                        keyword_score = 0.8
                        if keyword_score > best_score:
                            matches.append((product_id, keyword_score, {
                                'match_type': 'keyword',
                                'matched_text': keyword,
                                'product_data': product_data
                            }))
        
        # Sort by score and remove duplicates
        unique_matches = {}
        for product_id, score, context in matches:
            if product_id not in unique_matches or score > unique_matches[product_id][1]:
                unique_matches[product_id] = (product_id, score, context)
        
        result = list(unique_matches.values())
        result.sort(key=lambda x: x[1], reverse=True)
        return result[:10]  # Top 10 matches
    
    def detect_series(self, query: str) -> List[str]:
        """Detect product series mentioned in query"""
        detected_series = []
        query_lower = query.lower()
        
        for series_name, series_info in self.product_knowledge['series_info'].items():
            if series_name in query_lower:
                detected_series.append(series_name)
            else:
                # Check keywords
                for keyword in series_info['keywords']:
                    if keyword in query_lower:
                        detected_series.append(series_name)
                        break
        
        return detected_series


class KArrayAgenticRAG:
    """K-Array Agentic RAG system using LangGraph"""
    
    def __init__(self, vector_store: LocalVectorStore, llm_manager: LLMManager):
        if not LANGGRAPH_AVAILABLE:
            raise ImportError("LangGraph is required. Install with: pip install langgraph langchain")
        
        self.vector_store = vector_store
        self.llm_manager = llm_manager
        self.product_matcher = KArrayProductMatcher()
        self.setup_logging()
        
        # Create tools
        self.create_tools()
        
        # Build the workflow graph
        self.workflow = self.build_workflow()
    
    def setup_logging(self):
        """Setup logging"""
        self.logger = logging.getLogger(__name__)
    
    def create_tools(self):
        """Create tools for the RAG system"""
        
        @tool
        def search_k_array_products(query: str, top_k: int = 10) -> List[Dict[str, Any]]:
            """Search K-Array product database for relevant information."""
            try:
                results = self.vector_store.search(query=query, top_k=top_k)
                return results
            except Exception as e:
                self.logger.error(f"Error in search tool: {e}")
                return []
        
        @tool
        def fuzzy_search_products(query: str) -> List[Dict[str, Any]]:
            """Find products using fuzzy matching for typos and variations."""
            try:
                matches = self.product_matcher.fuzzy_match_products(query)
                
                # Convert matches to search results
                search_results = []
                for product_id, score, context in matches:
                    # Search for this specific product
                    product_results = self.vector_store.search(
                        query=product_id, 
                        top_k=3,
                        filters={'model': product_id} if hasattr(self.vector_store, 'search') else {}
                    )
                    
                    for result in product_results:
                        result['fuzzy_match_score'] = score
                        result['fuzzy_match_context'] = context
                        search_results.append(result)
                
                return search_results
            except Exception as e:
                self.logger.error(f"Error in fuzzy search tool: {e}")
                return []
        
        @tool
        def search_by_series(series_name: str, top_k: int = 5) -> List[Dict[str, Any]]:
            """Search for products by series (e.g., Kommander, Lyzard, Vyper)."""
            try:
                results = self.vector_store.search(
                    query=f"{series_name} series",
                    top_k=top_k,
                    filters={'product_line': series_name} if hasattr(self.vector_store, 'search') else {}
                )
                return results
            except Exception as e:
                self.logger.error(f"Error in series search tool: {e}")
                return []
        
        self.tools = [search_k_array_products, fuzzy_search_products, search_by_series]
        self.tool_node = ToolNode(self.tools)
    
    def build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""
        
        # Create the graph
        workflow = StateGraph(KArrayRAGState)
        
        # Add nodes
        workflow.add_node("analyze_query", self.analyze_query)
        workflow.add_node("search_tools", self.tool_node)
        workflow.add_node("evaluate_results", self.evaluate_results)
        workflow.add_node("refine_search", self.refine_search)
        workflow.add_node("generate_answer", self.generate_answer)
        
        # Add edges
        workflow.set_entry_point("analyze_query")
        
        workflow.add_edge("analyze_query", "search_tools")
        workflow.add_conditional_edges(
            "search_tools",
            self.should_evaluate_or_refine,
            {
                "evaluate": "evaluate_results",
                "refine": "refine_search"
            }
        )
        
        workflow.add_conditional_edges(
            "evaluate_results",
            self.should_continue_or_answer,
            {
                "continue": "refine_search",
                "answer": "generate_answer"
            }
        )
        
        workflow.add_edge("refine_search", "search_tools")
        workflow.add_edge("generate_answer", END)
        
        return workflow.compile()
    
    def analyze_query(self, state: KArrayRAGState) -> Dict[str, Any]:
        """Analyze the user query and prepare search strategy"""
        try:
            original_query = state["messages"][-1].content
            
            # Detect products using fuzzy matching
            product_matches = self.product_matcher.fuzzy_match_products(original_query)
            detected_products = [match[0] for match in product_matches if match[1] > 0.7]
            
            # Detect series
            detected_series = self.product_matcher.detect_series(original_query)
            
            # Create search strategy based on analysis
            processed_query = original_query
            
            # Enhance query with detected products and series
            if detected_products:
                processed_query += f" {' '.join(detected_products)}"
            if detected_series:
                processed_query += f" {' '.join(detected_series)}"
            
            self.logger.info(f"Query analysis - Original: {original_query}")
            self.logger.info(f"Detected products: {detected_products}")
            self.logger.info(f"Detected series: {detected_series}")
            
            # Create tool calls based on analysis
            tool_calls = []
            
            if detected_products:
                # Use fuzzy search for detected products
                tool_calls.append({
                    "tool": "fuzzy_search_products",
                    "args": {"query": original_query}
                })
            
            if detected_series:
                # Search by series
                for series in detected_series:
                    tool_calls.append({
                        "tool": "search_by_series", 
                        "args": {"series_name": series, "top_k": 5}
                    })
            
            # Always include general semantic search
            tool_calls.append({
                "tool": "search_k_array_products",
                "args": {"query": processed_query, "top_k": 8}
            })
            
            # Create AI message with tool calls
            ai_message = AIMessage(
                content="Analyzing query and searching for relevant K-Array products...",
                tool_calls=[
                    {
                        "name": call["tool"],
                        "args": call["args"],
                        "id": f"call_{i}"
                    }
                    for i, call in enumerate(tool_calls)
                ]
            )
            
            return {
                "messages": state["messages"] + [ai_message],
                "original_query": original_query,
                "processed_query": processed_query,
                "detected_products": detected_products,
                "iteration_count": 0,
                "needs_refinement": False
            }
            
        except Exception as e:
            self.logger.error(f"Error in query analysis: {e}")
            return {
                "messages": state["messages"] + [AIMessage(content="Error analyzing query")],
                "original_query": state.get("original_query", ""),
                "processed_query": state.get("original_query", ""),
                "detected_products": [],
                "iteration_count": 0,
                "needs_refinement": False
            }
    
    def should_evaluate_or_refine(self, state: KArrayRAGState) -> str:
        """Decide whether to evaluate results or refine search"""
        # Check if we have tool results
        last_message = state["messages"][-1]
        
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "evaluate"
        else:
            # If we have results from tools, evaluate
            return "evaluate"
    
    def evaluate_results(self, state: KArrayRAGState) -> Dict[str, Any]:
        """Evaluate search results using LLM"""
        try:
            # Collect all search results from tool messages
            search_results = []
            for message in reversed(state["messages"]):
                if hasattr(message, 'content') and isinstance(message.content, list):
                    for content_block in message.content:
                        if hasattr(content_block, 'content') and isinstance(content_block.content, str):
                            try:
                                result_data = json.loads(content_block.content)
                                if isinstance(result_data, list):
                                    search_results.extend(result_data)
                            except:
                                pass
            
            if not search_results:
                self.logger.warning("No search results found for evaluation")
                return {
                    **state,
                    "search_results": [],
                    "needs_refinement": True,
                    "evaluation_result": {"quality": "poor", "needs_refinement": True}
                }
            
            # Use LLM to evaluate results
            evaluation_prompt = f"""
            Evaluate these search results for the K-Array query: "{state['original_query']}"
            
            Search Results ({len(search_results)} documents):
            {json.dumps(search_results[:5], indent=2)}  # Show top 5 for evaluation
            
            Detected Products: {state.get('detected_products', [])}
            
            Evaluate and respond with JSON only:
            {{
                "quality": "excellent|good|fair|poor",
                "relevance_score": 0.0-1.0,
                "completeness": "complete|partial|incomplete",
                "needs_refinement": true/false,
                "missing_info": "what's missing if anything",
                "can_answer": true/false
            }}
            
            Consider:
            1. Do results contain the requested product information?
            2. Are technical specifications included if needed?
            3. Is the information accurate and detailed?
            """
            
            try:
                llm_response = self.llm_manager.generate_response(evaluation_prompt)
                
                # Extract JSON from response
                json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
                if json_match:
                    evaluation = json.loads(json_match.group())
                else:
                    evaluation = {"quality": "fair", "needs_refinement": False, "can_answer": True}
                
                self.logger.info(f"LLM Evaluation: {evaluation}")
                
                return {
                    **state,
                    "search_results": search_results,
                    "evaluation_result": evaluation,
                    "needs_refinement": evaluation.get("needs_refinement", False)
                }
                
            except Exception as e:
                self.logger.error(f"Error in LLM evaluation: {e}")
                return {
                    **state,
                    "search_results": search_results,
                    "evaluation_result": {"quality": "fair", "needs_refinement": False, "can_answer": True},
                    "needs_refinement": False
                }
                
        except Exception as e:
            self.logger.error(f"Error in result evaluation: {e}")
            return {
                **state,
                "search_results": [],
                "needs_refinement": True,
                "evaluation_result": {"quality": "poor", "needs_refinement": True}
            }
    
    def should_continue_or_answer(self, state: KArrayRAGState) -> str:
        """Decide whether to continue refining or generate final answer"""
        evaluation = state.get("evaluation_result", {})
        iteration_count = state.get("iteration_count", 0)
        
        # Stop if we've done too many iterations
        if iteration_count >= 2:
            return "answer"
        
        # Stop if results are good enough
        if not evaluation.get("needs_refinement", True):
            return "answer"
        
        # Stop if we can answer the question
        if evaluation.get("can_answer", False):
            return "answer"
        
        return "continue"
    
    def refine_search(self, state: KArrayRAGState) -> Dict[str, Any]:
        """Refine search strategy based on evaluation"""
        try:
            evaluation = state.get("evaluation_result", {})
            iteration_count = state.get("iteration_count", 0)
            
            # Create refined search strategy
            missing_info = evaluation.get("missing_info", "")
            original_query = state["original_query"]
            
            # Generate refined query
            refined_query = f"{original_query} {missing_info}".strip()
            
            # Try broader search
            tool_calls = [{
                "tool": "search_k_array_products",
                "args": {"query": refined_query, "top_k": 15}
            }]
            
            # Add series search if not done yet
            detected_series = self.product_matcher.detect_series(original_query)
            for series in detected_series:
                tool_calls.append({
                    "tool": "search_by_series",
                    "args": {"series_name": series, "top_k": 8}
                })
            
            ai_message = AIMessage(
                content=f"Refining search (iteration {iteration_count + 1})...",
                tool_calls=[
                    {
                        "name": call["tool"],
                        "args": call["args"],
                        "id": f"refine_call_{i}"
                    }
                    for i, call in enumerate(tool_calls)
                ]
            )
            
            return {
                **state,
                "messages": state["messages"] + [ai_message],
                "iteration_count": iteration_count + 1,
                "processed_query": refined_query
            }
            
        except Exception as e:
            self.logger.error(f"Error in search refinement: {e}")
            return {
                **state,
                "iteration_count": state.get("iteration_count", 0) + 1
            }
    
    def generate_answer(self, state: KArrayRAGState) -> Dict[str, Any]:
        """Generate final answer using all collected information"""
        try:
            search_results = state.get("search_results", [])
            original_query = state["original_query"]
            detected_products = state.get("detected_products", [])
            
            # Format results for answer generation
            formatted_results = self._format_results_for_answer(search_results)
            
            answer_prompt = f"""
            Generate a comprehensive answer for this K-Array technical query:
            
            USER QUERY: "{original_query}"
            DETECTED PRODUCTS: {detected_products}
            
            AVAILABLE INFORMATION:
            {formatted_results}
            
            INSTRUCTIONS:
            1. Provide accurate, specific technical information
            2. Include exact specifications with source attribution when available
            3. Use professional K-Array terminology
            4. If comparing products, create clear comparisons
            5. If information is missing, acknowledge it specifically
            6. Structure the answer logically
            7. Include relevant model numbers and series information
            8. Be helpful and comprehensive
            
            Generate a professional response that directly addresses the user's question.
            """
            
            try:
                final_answer = self.llm_manager.generate_response(answer_prompt)
                
                answer_message = AIMessage(content=final_answer)
                
                return {
                    **state,
                    "messages": state["messages"] + [answer_message],
                    "final_answer": final_answer
                }
                
            except Exception as e:
                self.logger.error(f"Error generating final answer: {e}")
                fallback_answer = "I apologize, but I encountered an error while generating the response. Please try rephrasing your question."
                
                return {
                    **state,
                    "messages": state["messages"] + [AIMessage(content=fallback_answer)],
                    "final_answer": fallback_answer
                }
                
        except Exception as e:
            self.logger.error(f"Error in answer generation: {e}")
            return state
    
    def _format_results_for_answer(self, results: List[Dict[str, Any]]) -> str:
        """Format search results for answer generation"""
        if not results:
            return "No relevant information found in the database."
        
        formatted_sections = []
        for i, result in enumerate(results[:10]):  # Top 10 results
            content = result.get('content', '')
            metadata = result.get('metadata', {})
            score = result.get('score', 0)
            
            section = f"""
            Document {i+1} (Relevance: {score:.3f}):
            Content: {content[:500]}{'...' if len(content) > 500 else ''}
            Product: {metadata.get('model', 'Unknown')}
            Series: {metadata.get('product_line', 'Unknown')}
            Category: {metadata.get('category', 'Unknown')}
            """
            formatted_sections.append(section)
        
        return "\n".join(formatted_sections)
    
    def process_query(self, user_query: str) -> str:
        """Process a user query through the agentic RAG workflow"""
        try:
            self.logger.info(f"Processing query with LangGraph: {user_query}")
            
            # Create initial state
            initial_state = KArrayRAGState(
                messages=[HumanMessage(content=user_query)],
                original_query=user_query,
                processed_query="",
                detected_products=[],
                search_results=[],
                evaluation_result=None,
                needs_refinement=False,
                iteration_count=0,
                final_answer=None
            )
            
            # Run the workflow
            final_state = self.workflow.invoke(initial_state)
            
            # Extract final answer
            final_answer = final_state.get("final_answer")
            if not final_answer:
                # Fallback: get last AI message
                for message in reversed(final_state["messages"]):
                    if isinstance(message, AIMessage) and message.content:
                        final_answer = message.content
                        break
            
            return final_answer or "I apologize, but I couldn't generate a response. Please try rephrasing your question."
            
        except Exception as e:
            self.logger.error(f"Error in workflow processing: {e}")
            return "I encountered an error while processing your query. Please try again."


# Update requirements.txt
def update_requirements():
    """Update requirements.txt with LangGraph dependencies"""
    new_requirements = [
        "langgraph>=0.2.0",
        "langchain>=0.3.0", 
        "langchain-core>=0.3.0"
    ]
    
    requirements_file = "/mnt/c/Users/nicco/Desktop/workspace/retrival/requirements.txt"
    
    try:
        with open(requirements_file, 'r') as f:
            existing = f.read()
        
        # Add new requirements if not present
        for req in new_requirements:
            package_name = req.split('>=')[0]
            if package_name not in existing:
                existing += f"\n{req}"
        
        with open(requirements_file, 'w') as f:
            f.write(existing)
        
        print("✅ Updated requirements.txt with LangGraph dependencies")
        
    except Exception as e:
        print(f"⚠️ Could not update requirements.txt: {e}")


if __name__ == "__main__":
    if not LANGGRAPH_AVAILABLE:
        print("❌ LangGraph not available!")
        print("📦 Install with: pip install langgraph langchain langchain-core")
        update_requirements()
        print("📝 Requirements updated. Run: pip install -r requirements.txt")
        exit(1)
    
    # Test the system
    from src.local_vector_store import LocalVectorStore
    from src.llm_manager import LLMManager
    
    print("🚀 Initializing K-Array Agentic RAG with LangGraph...")
    
    try:
        # Initialize components
        vector_store = LocalVectorStore()
        llm_manager = LLMManager()
        rag_system = KArrayAgenticRAG(vector_store, llm_manager)
        
        # Test problematic queries
        test_queries = [
            "mi dai informazioni sul K framework 3?",
            "mi dai informazioni sul ka208", 
            "Quali sono le specifiche del Kommander KA104?",
            "Differenze tra serie Lyzard e Vyper"
        ]
        
        for query in test_queries:
            print(f"\n{'='*80}")
            print(f"Query: {query}")
            print(f"{'='*80}")
            
            answer = rag_system.process_query(query)
            print("\n🤖 Answer:")
            print(answer)
            print("\n" + "-"*40)
    
    except Exception as e:
        print(f"❌ Error initializing system: {e}")
        print("Make sure vector store and LLM manager are properly configured.")