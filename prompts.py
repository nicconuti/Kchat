from typing import Dict
from functools import lru_cache

class LLMPrompts:
    """Centralized management of LLM prompt templates for clarity and maintainability."""
    
    @staticmethod
    def get_classification_prompt(categories_with_desc: Dict, filename: str, text_preview: str) -> str:
        """Generates the prompt for document classification."""
        category_definitions = "\n".join([f'- "{name}": {desc}' for name, desc in categories_with_desc.items()])
        return f"""
        You are an expert document classifier. Your task is to classify the document described below into ONE of the following categories.
        First, provide a brief `reasoning` text explaining your choice. Then, on a new line, provide a single, raw JSON object with "category" and "confidence" keys.
        
        **Categories:** {category_definitions}
        
        **Document Details:**
        - Filename: "{filename}"
        - Content Preview: "{text_preview}"
        
        **Response Format:**
        Reasoning: [Your brief reasoning here.]
        ```json
        {{"category": "your_chosen_category", "confidence": 0.95}}
        ```
        """
    
    PROMPT_VALIDATE_EXCEL_RECORD = """
    Hai il compito di validare e correggere un record estratto da un listino Excel tecnico.

    Record:
    - Serial: {serial}
    - Description: {description}
    - Price: {price}
    - Sheet name: {sheet_name}

    Se uno dei campi è mancante, incompleto o incoerente, correggilo.
    Restituisci un dizionario JSON nel formato:
    {{"serial": "...", "description": "...", "price": ...}}

    Mantieni il serial se è corretto. Non aggiungere campi extra.
    """


    @staticmethod
    def get_enrichment_prompt(chunk_text: str) -> str:
        """Generates the prompt for enriching a text chunk with metadata."""
        return f"""
        You are a metadata generation expert. For the following text chunk, generate a concise summary and three hypothetical questions that the chunk could answer.
        The summary should be short and informative. The questions should be relevant and answerable only with the provided text.
        
        Respond with a single, raw JSON object with keys: "chunk_summary" (string) and "hypothetical_questions" (list of strings).
        Do not include any markdown formatting or explanations.
        Do not include any thinking or reasoning in the answer.
        
        ---TEXT CHUNK---
        {chunk_text}
        ---END CHUNK---
        
        JSON:
        """
