class PipelineConfig:
    """Configurazioni per la pipeline di ingestione."""
    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".txt", ".html", ".htm", ".csv", ".json", ".xml"}

    SEMANTIC_CATEGORIES = {
        "product_price": "Documenti contenenti listini prezzi, offerte commerciali, preventivi o analisi costi.",
        "product_guide": "Manuali tecnici, guide utente, istruzioni di installazione o specifiche di prodotto.",
        "tech_assistance": "Rapporti di errore, guide alla risoluzione dei problemi, richieste di supporto tecnico o analisi dei problemi.",
        "software_assistance": "Guide all'installazione del software, procedure di aggiornamento, informazioni sulla licenza o problemi relativi al software.",
        "unclassified": "Documenti che non rientrano in nessuna delle altre categorie.",
    }

    MIN_EXTRACTED_TEXT_SIZE = 50
    FULL_TEXT_CLASSIFICATION_LIMIT = 8000
    TABLE_PREVIEW_ROWS = 1000

    # Configurazione del chunking
    CHUNK_SIZE = 1024
    CHUNK_OVERLAP = 128

    # Soglie di affidabilità
    LLM_CLASSIFICATION_THRESHOLD = 0.80
    CROSS_CHECK_CONFIDENCE_THRESHOLD = 0.95

    QUARANTINE_DIR = "quarantine"
    PRODUCT_STATUS_FIELD_NAME = "product_status"
