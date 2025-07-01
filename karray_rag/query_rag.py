import logging
import numpy as np
from typing import List, Optional, Set, Tuple
from rag_store import load_documents_from_jsonl # Manteniamo solo load
from haystack import Document
# Usiamo i componenti di SentenceTransformers
from haystack.components.embedders import SentenceTransformersTextEmbedder, SentenceTransformersDocumentEmbedder
from haystack.components.retrievers.in_memory import InMemoryEmbeddingRetriever
from haystack.document_stores.in_memory import InMemoryDocumentStore
from sentence_transformers import SentenceTransformer # Per il warm-up e scelta modello
from sklearn.metrics.pairwise import cosine_similarity
import re # Per il cleaning e l'evidenziazione

# Importa CrossEncoder per il reranking
from sentence_transformers import CrossEncoder

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

INPUT_FILE = "data/embedded_karray_documents.jsonl"

# Modelli di alta qualità per l'embedding (prioritari)
# Questi sono modelli all-in-one che funzionano bene per query e documenti.
EMBEDDING_MODELS = [
    "BAAI/bge-large-en-v1.5",       # Generalmente eccellente
    "sentence-transformers/all-mpnet-base-v2",  # Ottimo compromesso performance/qualità
    "intfloat/e5-large-v2",                     # Molto buono per compiti di simmetria (query-documento)
]

# Modello per il reranking (Cross-Encoder) - Necessita di un modello specifico
# Questo modello calcola uno score di rilevanza tra query e documento.
RERANKING_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2" # Un buon modello leggero per reranking
# Altri possibili: "cross-encoder/ms-marco-MMarco-ms-v2" (multilingue, più grande)

class EnhancedRetriever:
    def __init__(self, documents: List[Document], embedding_model_name: Optional[str] = None, reranker_model_name: Optional[str] = None):
        self.documents = documents
        # Scegli il modello di embedding basato sulla disponibilità
        self.embedding_model_name = embedding_model_name or self._choose_best_embedding_model()
        self.reranker_model_name = reranker_model_name or RERANKING_MODEL
        self.setup_retrieval_system()
        
    def _choose_best_embedding_model(self) -> str:
        """Sceglie il miglior modello di embedding disponibile tra EMBEDDING_MODELS."""
        for model in EMBEDDING_MODELS:
            try:
                # Tentativo di caricamento per verificare la disponibilità
                SentenceTransformer(model)
                logger.info(f"✅ Modello di embedding selezionato: {model}")
                return model
            except Exception as e:
                logger.warning(f"⚠️ Modello di embedding '{model}' non disponibile localmente o errore nel caricamento: {e}. Provando il prossimo...")
                continue
        logger.error("❌ Nessun modello di embedding configurato disponibile. Usando il fallback predefinito di Haystack.")
        return EMBEDDING_MODELS[0] # Ritorna il primo come fallback (potrebbe fallire)

    def setup_retrieval_system(self):
        """Configura il sistema di retrieval con modelli di alta qualità e reranking."""
        logger.info(f"🧠 Inizializzazione con modello di embedding: {self.embedding_model_name}")
        logger.info(f"✨ Inizializzazione reranker con modello: {self.reranker_model_name}")
        
        # Embedder per testo (query)
        self.text_embedder = SentenceTransformersTextEmbedder(
            model=self.embedding_model_name,
            normalize_embeddings=True
        )
        # Embedder per documenti
        self.document_embedder = SentenceTransformersDocumentEmbedder(
            model=self.embedding_model_name,
            normalize_embeddings=True
        )
        
        # Inizializzazione del reranker CrossEncoder
        # Non è un componente Haystack diretto, ma una libreria esterna usata nel reranking_results
        self.cross_reranker = CrossEncoder(self.reranker_model_name)
        
        # Warm up degli embedders e del reranker
        logger.info("🔥 Warm up degli embedders e del reranker...")
        self.text_embedder.warm_up()
        self.document_embedder.warm_up()
        # Per CrossEncoder, una chiamata di prova
        try:
            self.cross_reranker.predict([("test query", "test document content")])
        except Exception as e:
            logger.error(f"❌ Errore durante il warm up del reranker: {e}")
        
        # Documento store
        self.document_store = InMemoryDocumentStore()
        
        # Re-embed e pulisci i documenti all'avvio
        logger.info("📄 Re-embedding e pulizia documenti con modello di qualità superiore...")
        embedded_docs = self.re_embed_documents()
        if embedded_docs:
            self.document_store.write_documents(embedded_docs)
            logger.info(f"✅ Caricati {len(embedded_docs)} documenti nello store.")
        else:
            logger.error("❌ Nessun documento valido da caricare nel document store!")
            
        # Retriever con configurazione ottimizzata
        self.retriever = InMemoryEmbeddingRetriever(
            document_store=self.document_store,
            top_k=20  # Recupera più documenti per permettere al reranker di lavorare meglio
        )
        
        logger.info("✅ Sistema di retrieval avanzato inizializzato con successo!")
    
    def re_embed_documents(self) -> List[Document]:
        """
        Re-embedda i documenti e pulisce quelli con embedding non validi.
        Viene chiamato solo una volta all'inizializzazione.
        """
        docs_to_embed = []
        for doc in self.documents:
            # Assicurati che il contenuto sia una stringa e non vuoto
            if not doc.content or not isinstance(doc.content, str) or not doc.content.strip():
                logger.warning(f"⚠️ Saltato documento con contenuto vuoto o non stringa: {doc.meta}")
                continue
            
            # Crea nuovi documenti senza embedding per forzare il re-embedding
            # Importante: Mantieni l'ID originale se il documento proviene da un chunking precedente
            new_doc = Document(
                content=doc.content.strip(),
                meta=doc.meta.copy() if doc.meta else {},
                id=doc.id # Mantiene l'ID originale del Documento Haystack
            )
            docs_to_embed.append(new_doc)
        
        if not docs_to_embed:
            logger.error("❌ Nessun documento valido da embeddare per il retrieval!")
            return []
        
        logger.info(f"Embedding di {len(docs_to_embed)} documenti per il document store...")
        try:
            result = self.document_embedder.run(documents=docs_to_embed)
            embedded_docs = result["documents"]
        except Exception as e:
            logger.error(f"❌ Errore durante il re-embedding dei documenti: {e}")
            return []

        # Verifica e pulisci embeddings NaN
        clean_docs = []
        for doc in embedded_docs:
            if hasattr(doc, 'embedding') and doc.embedding is not None:
                embedding_array = np.array(doc.embedding)
                if not np.isnan(embedding_array).any() and embedding_array.size > 0:
                    clean_docs.append(doc)
                else:
                    logger.warning(f"⚠️ Embedding NaN/vuoto trovato, saltato documento: {doc.meta.get('source', 'N/A')}")
            else:
                logger.warning(f"⚠️ Embedding mancante dopo il processo, saltato documento: {doc.meta.get('source', 'N/A')}")
        
        logger.info(f"✅ Documenti validi con embedding dopo pulizia: {len(clean_docs)}/{len(embedded_docs)}")
        return clean_docs
    
    def rerank_results(self, query: str, initial_results: List[Document]) -> List[Tuple[Document, float, float, float, float]]:
        """
        Re-ranking avanzato che combina:
        1. Score del Cross-Encoder (il più importante per la rilevanza)
        2. Similarità coseno (dal modello di embedding iniziale)
        3. Bonus per matching di keywords esatte
        4. Bonus per lunghezza documento
        """
        if not initial_results:
            return []
        
        # 1. Calcola gli score del Cross-Encoder
        sentence_pairs = [(query, doc.content) for doc in initial_results]
        try:
            cross_scores = self.cross_reranker.predict(sentence_pairs)
        except Exception as e:
            logger.error(f"❌ Errore durante il calcolo degli score del Cross-Encoder: {e}")
            cross_scores = [-1.0] * len(initial_results) # Fallback a score bassi

        scored_docs_detailed = []
        
        # Embedding della query per il cosine_sim (già calcolato nel search, ma ri-calcoliamo per chiarezza)
        query_embedding_result = self.text_embedder.run(text=query)
        query_embedding = np.array(query_embedding_result["embedding"]).reshape(1, -1)

        for i, doc in enumerate(initial_results):
            try:
                # Verifica validità dell'embedding del documento
                if not hasattr(doc, 'embedding') or doc.embedding is None:
                    continue
                doc_embedding = np.array(doc.embedding).reshape(1, -1)
                if np.isnan(doc_embedding).any() or doc_embedding.size == 0:
                    logger.warning(f"⚠️ Documento con embedding NaN/vuoto nel reranking, saltato: {doc.meta.get('source', 'N/A')}")
                    continue
                
                # Similarità coseno (dal modello iniziale)
                cosine_sim = cosine_similarity(query_embedding, doc_embedding)[0][0]
                if np.isnan(cosine_sim):
                    cosine_sim = 0.0 # Gestisci NaN per la similarità coseno
                
                cross_encoder_score = float(cross_scores[i]) # Assicurati che sia float

                # Bonus per matching di keywords esatte (ponderazione inferiore rispetto alla similarità)
                keyword_bonus = self.calculate_keyword_bonus(query.lower(), doc.content.lower()) * 0.1 # Max 10% bonus
                
                # Bonus per lunghezza documento (documenti più lunghi possono contenere più info)
                # Normalizzato tra 0 e 0.05 (max 5% bonus)
                length_bonus = min(len(doc.content) / 2000, 0.05) 
                
                # Score finale combinato
                # Il Cross-Encoder è il componente più importante, quindi gli diamo peso maggiore.
                # Normalizziamo il cross_encoder_score per essere tra 0 e 1 se non lo è già.
                # I modelli CrossEncoder di solito output score arbitrari, ma una sigmoid può normalizzare
                # una semplice normalizzazione min-max su un batch può essere rischiosa.
                # Meglio affidarsi alla sua scala originale e ponderarla.
                
                # Esempio di combinazione:
                # cross_encoder_score (tipicamente -x a +x, convertiamo in scala più utile, es. 0 a 1)
                # Se il modello è addestrato a dare score alti per rilevante, bassi per non rilevante,
                # potremmo volerlo pesare direttamente.
                # Molti modelli MS MARCO output score che sono logits, non probabilità.
                # Un semplice re-scaling o un sigmoide potrebbe essere utile per combinare.
                # Per semplicità, ipotizziamo che un cross_encoder_score più alto sia migliore.
                
                # Ponderazioni: Cross-Encoder molto importante, poi Cosine, poi bonus minori
                # Regolare questi pesi è una parte chiave dell'ottimizzazione!
                final_score = (cross_encoder_score * 0.7) + (cosine_sim * 0.2) + keyword_bonus + length_bonus
                
                scored_docs_detailed.append((doc, final_score, cross_encoder_score, cosine_sim, keyword_bonus, length_bonus))
                
            except Exception as e:
                logger.warning(f"⚠️ Errore processing documento nel reranking: {e}. Doc Source: {doc.meta.get('source', 'N/A')}")
                continue
        
        if not scored_docs_detailed:
            logger.warning("⚠️ Nessun documento valido dopo il re-ranking.")
            return []
        
        # Ordina per score finale (decrescente)
        scored_docs_detailed.sort(key=lambda x: x[1], reverse=True)
        
        return scored_docs_detailed
    
    def calculate_keyword_bonus(self, query: str, content: str) -> float:
        """
        Calcola un bonus per la presenza di parole chiave esatte della query nel contenuto.
        Ignora parole molto corte per ridurre il rumore.
        """
        query_words = set(re.findall(r'\b\w+\b', query.lower())) # Estrai solo parole alfanumeriche
        content_words = set(re.findall(r'\b\w+\b', content.lower()))
        
        # Filtra parole molto corte o comuni (stop words)
        query_words = {word for word in query_words if len(word) > 2 and word not in self._get_common_stopwords()}
        
        if not query_words:
            return 0.0
        
        common_words = query_words.intersection(content_words)
        
        # Bonus proporzionale al numero di parole chiave della query che matchano
        return len(common_words) / len(query_words)
    
    def _get_common_stopwords(self) -> Set[str]:
        """Restituisce un set di stop words comuni (può essere esteso)."""
        return {"il", "la", "i", "gli", "le", "un", "una", "di", "a", "da", "in", "con", "su", "per", "tra", "fra", "e", "o", "ma", "si", "no", "non", "che", "cosa", "come", "dove", "quando", "perché", "chi", "quale", "quali", "cui"}

    def search(self, query: str, top_k: int = 5) -> List[Tuple[Document, float, float, float, float]]:
        """
        Esegue la ricerca avanzata con retrieval iniziale e successivo re-ranking.
        Ritorna una lista di tuple: (documento, score_finale, cross_score, cosine_sim, keyword_bonus).
        """
        logger.info(f"🔍 Avvio ricerca avanzata per: '{query}'")
        
        if not query or not query.strip():
            logger.warning("⚠️ Query vuota! Restituisco risultati vuoti.")
            return []
        
        try:
            # 1. Embedding della query
            query_result = self.text_embedder.run(text=query.strip())
            query_embedding = query_result["embedding"]
            
            if np.isnan(np.array(query_embedding)).any():
                logger.error("❌ Query embedding contiene NaN! Non posso procedere con il retrieval.")
                return []
            
            # 2. Retrieval iniziale (recupera un numero maggiore di candidati)
            initial_results_haystack = self.retriever.run(
                query_embedding=query_embedding,
                top_k=self.retriever.top_k # Usa il top_k configurato nel retriever (es. 20)
            )
            
            initial_documents = initial_results_haystack.get("documents", [])
            if not initial_documents:
                logger.warning("⚠️ Nessun documento trovato nel retrieval iniziale.")
                return []
            
            logger.info(f"Recuperati {len(initial_documents)} documenti candidati nel retrieval iniziale.")

            # 3. Re-ranking avanzato
            reranked_results_detailed = self.rerank_results(query, initial_documents)
            
            if not reranked_results_detailed:
                logger.warning("⚠️ Nessun documento valido dopo il re-ranking.")
                return []
            
            # 4. Ritorna i top_k risultati finali
            return reranked_results_detailed[:top_k]
            
        except Exception as e:
            logger.error(f"❌ Errore critico durante la ricerca: {e}", exc_info=True) # exc_info per stack trace
            return []

def main():
    logger.info("📥 Caricamento documenti embedded...")
    documents = load_documents_from_jsonl(INPUT_FILE)
    if not documents:
        logger.error("❌ Nessun documento embedded trovato. Esegui embed_karray.py prima per generare gli embedding.")
        return

    logger.info(f"📄 Caricati {len(documents)} documenti pronti per il retrieval.")
    
    # Inizializza sistema di retrieval avanzato
    # Lasciamo che EnhancedRetriever scelga il miglior modello di embedding disponibile
    retriever = EnhancedRetriever(documents) # Non passiamo model_name, lo sceglierà la classe
    
    print("\n🎯 Sistema di Retrieval Avanzato attivo!")
    print("💡 Ottimizzato per qualità massima - le query potrebbero essere leggermente più lente per via del re-ranking.")
    print("💬 Scrivi una domanda (Ctrl+C per uscire)")
    
    while True:
        try:
            query = input("\n🔍 > ").strip()
            if not query:
                continue
            
            # Ricerca avanzata
            # top_k qui si riferisce al numero di risultati finali da mostrare
            results = retriever.search(query, top_k=5) 
            
            if not results:
                print("❌ Nessun documento rilevante trovato.")
                continue

            print(f"\n📋 Trovati {len(results)} documenti rilevanti (con score avanzato):")
            print("=" * 90)
            
            for i, (doc, final_score, cross_score, cosine_sim, keyword_bonus, length_bonus) in enumerate(results, 1):
                source = doc.meta.get('source', 'fonte sconosciuta')
                # Recupera l'ID del chunk e l'ID del documento originale (se presenti)
                chunk_id = doc.meta.get('chunk_id', 'N/A')
                original_doc_id = doc.meta.get('original_source_doc_id', 'N/A')

                print(f"\n[{i}] 📄 Fonte: {source}")
                print(f"    🔗 Chunk ID: {chunk_id}, Original Doc ID: {original_doc_id}")
                print(f"    📊 Score Finale: {final_score:.4f}")
                print(f"    🌟 Cross-Encoder Score: {cross_score:.4f}")
                print(f"    🎯 Cosine Similarity (initial): {cosine_sim:.4f}")
                print(f"    🔑 Keyword Bonus: {keyword_bonus:.4f}")
                print(f"    📏 Length Bonus: {length_bonus:.4f}")
                print("    📝 Contenuto:")
                
                content_preview = doc.content[:800] # Aumentato preview
                if len(doc.content) > 800:
                    content_preview += "..."
                
                # Evidenzia keywords nella preview, ignorando la case
                query_words = re.findall(r'\b\w+\b', query.lower()) # Estrai solo parole
                for word in query_words:
                    if len(word) > 2 and word not in retriever._get_common_stopwords(): # Solo parole significative
                        # Usa re.sub con una funzione di sostituzione per gestire la case originale
                        content_preview = re.sub(
                            r'(?i)\b(' + re.escape(word) + r')\b', # (?i) per case-insensitive, \b per intere parole
                            r'**\1**', # \1 si riferisce al gruppo catturato (la parola)
                            content_preview
                        )
                
                print(f"    {content_preview}")
                print("-" * 70) # Linea separatrice più lunga

        except KeyboardInterrupt:
            print("\n👋 Uscita dal sistema di retrieval avanzato.")
            break
        except Exception as e:
            logger.error(f"❌ Errore critico durante la query principale: {e}", exc_info=True)


if __name__ == "__main__":
    main()