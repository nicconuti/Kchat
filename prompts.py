from typing import Dict

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

    @staticmethod
    def get_structured_extraction_prompt(sheet_preview: str, sheet_name: str) -> str:
        """Generates a dynamic prompt for extracting structured data from table-like text."""
        return f"""
        You are an exceptionally accurate and reliable data extraction engine. Your primary objective is to extract product data without hallucination from the provided text, which represents rows from a spreadsheet named '{sheet_name}'.

        Your output must be a strict JSON array. Each object in the array must represent a product and MUST contain the following keys:
        
        "serial": (Product identifier, mapped from column names like "serial", "SKU", "model", "SN", "S/N", "P/N", "product_code", "part_number")
        "description": (Product description; can be null if missing. Never include any data not explicitly described in the source.)
        "price": (Numeric value for the price, use null if missing; remove currency symbols and ensure all values are numeric, including decimals, e.g., 420.00).

        Important Instructions for the "serial" key:
        The source data may use various headers for the product identifier. Be vigilant for columns like "serial", "SKU", "model", "SN", "S/N", "P/N", "product_code", "part_number", or similar variations.
        If the "description" or "price" fields are missing or incomplete, set them to null. Do not make assumptions or invent missing data.
        Prices should always be treated as numeric values (e.g., 450.00). If multiple columns contain price-related data, combine them appropriately and discard non-numeric characters.

        If the spreadsheet contains headers or summary rows with product identifiers, treat these identifiers as part of the 'description' field if applicable.

        Data Completeness and Accuracy:
        If either the "price" or "description" value is not explicitly present in a row, you MUST use null for that field. Do not infer or hallucinate missing data.

        Output ONLY the raw JSON array. Do not include any introductory text, explanations, markdown formatting (like code blocks), or other extraneous characters. Your response must begin directly with [ and end with ].        
        Do not include any thinking or reasoning in the answer.

        ---SHEET PREVIEW---
        {sheet_preview}
        ---END PREVIEW---

        JSON:
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
