#!/usr/bin/env python3
"""
Dynamic Configuration System for K-Array Chat System
Removes hardcoded values and provides configurable parameters
"""

import json
import os
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class RetrievalConfig:
    """Configuration for retrieval strategies"""
    exact_product_weight: float = 0.25
    qa_pairs_weight: float = 0.20
    technical_specs_weight: float = 0.18
    semantic_chunks_weight: float = 0.15
    searchable_content_weight: float = 0.12
    hybrid_search_weight: float = 0.10
    
    # Query transformation settings
    enable_semantic_expansion: bool = True
    enable_product_focused_transform: bool = True
    enable_technical_transform: bool = True
    
    # Reranking settings
    semantic_weight: float = 0.7
    rerank_weight: float = 0.3
    

@dataclass
class CacheConfig:
    """Configuration for caching strategies"""
    domain_knowledge_ttl_hours: int = 24
    vector_store_cache_ttl_hours: int = 168  # 1 week
    llm_response_cache_ttl_minutes: int = 60
    enable_persistent_cache: bool = True
    cache_directory: str = "./data/cache"


@dataclass
class ServerConfig:
    """Configuration for server settings"""
    host: str = "0.0.0.0"
    port: int = 7860
    debug: bool = True
    share: bool = False
    max_request_size: int = 50 * 1024 * 1024  # 50MB
    

@dataclass
class VectorStoreConfig:
    """Configuration for vector store"""
    collection_name: str = "k_array_enhanced"
    embedding_dimension: int = 768
    embedding_model: str = "all-mpnet-base-v2"
    index_type: str = "IVF_FLAT"
    metric_type: str = "IP"
    nlist: int = 1024
    host: str = "localhost"
    port: str = "19530"


@dataclass
class LLMConfig:
    """Configuration for LLM settings"""
    default_max_tokens: int = 1000
    default_temperature: float = 0.7
    translation_temperature: float = 0.3
    analysis_temperature: float = 0.5
    enable_query_intelligence: bool = True
    enable_fallback_provider: bool = True


class DynamicConfigManager:
    """Manages dynamic configuration with file-based overrides"""
    
    def __init__(self, config_file: str = "config/dynamic_config.json"):
        self.config_file = config_file
        self.logger = logging.getLogger(__name__)
        
        # Default configurations
        self.retrieval_config = RetrievalConfig()
        self.cache_config = CacheConfig()
        self.server_config = ServerConfig()
        self.vector_store_config = VectorStoreConfig()
        self.llm_config = LLMConfig()
        
        # Load overrides from file
        self.load_config()
        
        # Dynamic domain knowledge
        self._domain_knowledge = None
        self._domain_knowledge_file = "config/domain_knowledge.json"
        
    def load_config(self):
        """Load configuration from file if it exists"""
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                
                # Update configurations with loaded values
                if 'retrieval' in config_data:
                    self._update_dataclass(self.retrieval_config, config_data['retrieval'])
                
                if 'cache' in config_data:
                    self._update_dataclass(self.cache_config, config_data['cache'])
                
                if 'server' in config_data:
                    self._update_dataclass(self.server_config, config_data['server'])
                
                if 'vector_store' in config_data:
                    self._update_dataclass(self.vector_store_config, config_data['vector_store'])
                
                if 'llm' in config_data:
                    self._update_dataclass(self.llm_config, config_data['llm'])
                
                self.logger.info(f"Configuration loaded from {self.config_file}")
                
            except Exception as e:
                self.logger.warning(f"Failed to load config from {self.config_file}: {e}")
    
    def _update_dataclass(self, dataclass_instance, update_dict: Dict[str, Any]):
        """Update dataclass instance with dictionary values"""
        for key, value in update_dict.items():
            if hasattr(dataclass_instance, key):
                setattr(dataclass_instance, key, value)
    
    def save_config(self):
        """Save current configuration to file"""
        
        try:
            # Create config directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            config_data = {
                'retrieval': asdict(self.retrieval_config),
                'cache': asdict(self.cache_config),
                'server': asdict(self.server_config),
                'vector_store': asdict(self.vector_store_config),
                'llm': asdict(self.llm_config),
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            self.logger.info(f"Configuration saved to {self.config_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save config to {self.config_file}: {e}")
    
    def get_domain_knowledge(self) -> Optional[Dict[str, Any]]:
        """Get domain knowledge from file"""
        
        if self._domain_knowledge is not None:
            return self._domain_knowledge
        
        if os.path.exists(self._domain_knowledge_file):
            try:
                with open(self._domain_knowledge_file, 'r') as f:
                    self._domain_knowledge = json.load(f)
                return self._domain_knowledge
            except Exception as e:
                self.logger.warning(f"Failed to load domain knowledge: {e}")
        
        return None
    
    def save_domain_knowledge(self, knowledge: Dict[str, Any]):
        """Save domain knowledge to file"""
        
        try:
            os.makedirs(os.path.dirname(self._domain_knowledge_file), exist_ok=True)
            
            with open(self._domain_knowledge_file, 'w') as f:
                json.dump(knowledge, f, indent=2)
            
            self._domain_knowledge = knowledge
            self.logger.info(f"Domain knowledge saved to {self._domain_knowledge_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save domain knowledge: {e}")
    
    def update_retrieval_weights(self, weights: Dict[str, float]):
        """Update retrieval strategy weights"""
        
        for strategy, weight in weights.items():
            if hasattr(self.retrieval_config, f"{strategy}_weight"):
                setattr(self.retrieval_config, f"{strategy}_weight", weight)
        
        self.save_config()
        self.logger.info("Retrieval weights updated")
    
    def get_query_expansions(self) -> Dict[str, str]:
        """Get query expansion rules from config or defaults"""
        
        domain_knowledge = self.get_domain_knowledge()
        if domain_knowledge and 'query_expansions' in domain_knowledge:
            return domain_knowledge['query_expansions']
        
        # Default expansions
        return {
            'power': 'power watt output',
            'size': 'dimensions weight physical',
            'connect': 'connectivity input output interface',
            'install': 'installation mounting setup configuration',
            'spec': 'specifications technical details',
            'app': 'applications use cases installations'
        }
    
    def get_confidence_thresholds(self) -> Dict[str, float]:
        """Get confidence thresholds for various operations"""
        
        return {
            'language_detection_min': 0.6,
            'intent_analysis_min': 0.7,
            'clarification_threshold': 0.6,
            'reranking_confidence_boost': 0.1,
            'multi_vector_confidence_min': 0.5
        }
    
    def create_default_config_file(self):
        """Create a default configuration file for user customization"""
        
        default_config = {
            "retrieval": {
                "exact_product_weight": 0.25,
                "qa_pairs_weight": 0.20,
                "technical_specs_weight": 0.18,
                "semantic_chunks_weight": 0.15,
                "searchable_content_weight": 0.12,
                "hybrid_search_weight": 0.10,
                "enable_semantic_expansion": True,
                "enable_product_focused_transform": True,
                "enable_technical_transform": True,
                "semantic_weight": 0.7,
                "rerank_weight": 0.3
            },
            "cache": {
                "domain_knowledge_ttl_hours": 24,
                "vector_store_cache_ttl_hours": 168,
                "llm_response_cache_ttl_minutes": 60,
                "enable_persistent_cache": True,
                "cache_directory": "./data/cache"
            },
            "server": {
                "host": "0.0.0.0",
                "port": 7860,
                "debug": True,
                "share": False,
                "max_request_size": 52428800
            },
            "vector_store": {
                "collection_name": "k_array_enhanced",
                "embedding_dimension": 768,
                "embedding_model": "all-mpnet-base-v2",
                "index_type": "IVF_FLAT",
                "metric_type": "IP",
                "nlist": 1024,
                "host": "localhost",
                "port": "19530"
            },
            "llm": {
                "default_max_tokens": 1000,
                "default_temperature": 0.7,
                "translation_temperature": 0.3,
                "analysis_temperature": 0.5,
                "enable_query_intelligence": True,
                "enable_fallback_provider": True
            }
        }
        
        try:
            os.makedirs("config", exist_ok=True)
            
            with open("config/dynamic_config.json", 'w') as f:
                json.dump(default_config, f, indent=2)
            
            # Also create domain knowledge template
            domain_template = {
                "product_series": {
                    "kommander": ["ka02i", "ka04", "ka08", "ka102", "ka104"],
                    "lyzard": ["kz1", "kz7", "kz14", "kz26"],
                    "vyper": ["kv25", "kv52"],
                    "python": ["kp102", "kp52", "kp25"],
                    "firenze": ["ks4p", "ks7p", "ks10p"],
                    "azimut": ["kamut2l", "kamut2v25"]
                },
                "technical_categories": [
                    "power_output", "frequency_response", "dimensions", "weight",
                    "impedance", "spl", "connectivity", "mounting", "materials"
                ],
                "application_categories": [
                    "hospitality", "retail", "museums", "theaters", "restaurants",
                    "hotels", "fitness", "marine", "worship", "corporate"
                ],
                "query_expansions": {
                    "power": "power watt output",
                    "size": "dimensions weight physical",
                    "connect": "connectivity input output interface",
                    "install": "installation mounting setup configuration"
                },
                "last_updated": datetime.now().isoformat()
            }
            
            with open("config/domain_knowledge.json", 'w') as f:
                json.dump(domain_template, f, indent=2)
            
            print("✅ Default configuration files created in config/ directory")
            print("📝 Edit config/dynamic_config.json to customize system behavior")
            print("📝 Edit config/domain_knowledge.json to add/modify K-Array products")
            
        except Exception as e:
            print(f"❌ Failed to create config files: {e}")


# Global configuration instance
dynamic_config = DynamicConfigManager()


if __name__ == "__main__":
    # Create default configuration files
    dynamic_config.create_default_config_file()