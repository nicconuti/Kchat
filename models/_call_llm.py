import logging
import os

# Initialize logger early
_logger = logging.getLogger(__name__)

# Configuration for critical dependency handling
FAIL_FAST_ON_MISSING_DEPS = os.getenv("KCHAT_FAIL_FAST", "false").lower() == "true"

try:
    import ollama
    OLLAMA_AVAILABLE = True
    _logger.info("✅ Ollama package loaded successfully")
except ImportError as e:
    OLLAMA_AVAILABLE = False
    error_msg = f"❌ CRITICAL: Ollama package not available - {e}"
    
    if FAIL_FAST_ON_MISSING_DEPS:
        _logger.critical(error_msg)
        _logger.critical("Set KCHAT_FAIL_FAST=false to use stub mode")
        raise ImportError("Ollama is required for production deployment") from e
    
    _logger.warning(error_msg)
    _logger.warning("⚠️ Using stub client - responses will be empty!")
    _logger.warning("Install ollama: pip install ollama")
    
    class _OllamaStub:
        def __init__(self):
            _logger.warning("🔧 Ollama stub client initialized")
        
        def ps(self):
            _logger.warning("Stub ps() called - no models available")
            return {"models": []}

        def list(self):
            _logger.warning("Stub list() called - no models available") 
            return {"models": []}

        def chat(self, *args, **kwargs):
            _logger.warning("Stub chat() called - returning empty response")
            if kwargs.get("stream"):
                yield {"message": {"content": ""}, "done": True}
            return {"message": {"content": ""}}

    ollama = _OllamaStub()

import json
import time
from typing import Iterator, Literal, Dict, Any, Optional, List
from agents.context import AgentContext
# --- Configurazione e Tipi ---

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

ModelName = Literal[
    "mistral",
    "openchat",
    "deepseek-r1:8b",     # Versione standard
    "deepseek-coder:6.7b-instruct", #Versione instructed
    "deepseek-r1:14b",    # Versione più potente
    "llama3:8b-instruct"
]

# Conversation history management implemented in call_with_context and stream_with_context methods 

# --- Classe Client per Ollama ---
#1.  [User Input] 
#2.  [ContextManager] = aggiorna history, estrae contesto (lingua, topic, entità)
#3.  [LanguageAgent] = rileva lingua
#4.  [TranslationAgent] = input → lingua pivot (ENG), solo se necessario
#5.  [IntentAgent] = rileva intento, entità e task
#6.  [DocumentRetrieverAgent] = RAG con filtro lingua
#      →   se top-k score basso → trigger fallback
#7.  [LLM ClarificationAgent] = se ambiguo
#8.  [ActionExecutor] = se serve crea_preventivo, trouble shouting, etc.
#9.  [LLM Responder (openchat)] = genera risposta (ENG o originale)
#10. [TranslationAgent] = ENG → lingua utente (se serve)
#11. [LLM Verifier] = check grounding, tono, correttezza
#12. [ContextManager] = aggiorna history assistente
#13. [Logger] = scrive trace completa
#14. [Frontend] = mostra output



class LLMClient:
    """
    Un client per interagire con i modelli locali di Ollama.
    Centralizza la logica di chiamata, streaming e gestione degli errori.
    Versione production-ready con connection pooling e fallback robusti.
    """
    def __init__(
        self, 
        default_model: ModelName = "mistral",
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: float = 30.0,
        health_check_interval: int = 60
    ):
        self.default_model = default_model
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.health_check_interval = health_check_interval
        self.last_health_check = 0
        self.is_healthy = False
        self.available_models = set()
        
        # Initialize connection
        self._initialize_connection()

    def _initialize_connection(self) -> None:
        """Inizializza la connessione con Ollama e verifica i modelli disponibili."""
        try:
            # Verifica la connessione con Ollama
            models_response = ollama.ps()
            self.is_healthy = True
            self.last_health_check = time.time()
            
            # Aggiorna la lista dei modelli disponibili
            self._update_available_models()
            
            logger.info(f"Connessione con Ollama stabilita. Modelli disponibili: {len(self.available_models)}")
            
        except Exception as e:
            self.is_healthy = False
            logger.error(f"Impossibile connettersi a Ollama. Errore: {e}")
            # Non sollevare l'eccezione per permettere il graceful degradation
            
    def _update_available_models(self) -> None:
        """Aggiorna la lista dei modelli disponibili."""
        try:
            models_list = ollama.list()
            if 'models' in models_list:
                self.available_models = {model['name'] for model in models_list['models']}
                logger.debug(f"Modelli disponibili aggiornati: {self.available_models}")
        except Exception as e:
            logger.warning(f"Impossibile aggiornare la lista dei modelli: {e}")

    def _health_check(self) -> bool:
        """Verifica la salute della connessione se necessario."""
        current_time = time.time()
        if current_time - self.last_health_check > self.health_check_interval:
            try:
                ollama.ps()
                self.is_healthy = True
                self._update_available_models()
                logger.debug("Health check Ollama completato con successo")
            except Exception as e:
                self.is_healthy = False
                logger.warning(f"Health check Ollama fallito: {e}")
            finally:
                self.last_health_check = current_time
        
        return self.is_healthy

    def _validate_model(self, model: str) -> str:
        """Valida e restituisce un modello disponibile."""
        if not self._health_check():
            logger.warning("Ollama non disponibile, uso modello di default")
            return self.default_model
        
        # Se il modello richiesto è disponibile, usalo
        if model in self.available_models:
            return model
        
        # Altrimenti, cerca un modello simile
        for available_model in self.available_models:
            if model.split(':')[0] in available_model:
                logger.info(f"Modello {model} non trovato, uso {available_model}")
                return available_model
        
        # Fallback al modello di default
        if self.default_model in self.available_models:
            logger.warning(f"Modello {model} non disponibile, uso default {self.default_model}")
            return self.default_model
        
        # Se anche il default non è disponibile, usa il primo disponibile
        if self.available_models:
            fallback_model = next(iter(self.available_models))
            logger.warning(f"Nessun modello preferito disponibile, uso {fallback_model}")
            return fallback_model
        
        # Se non ci sono modelli disponibili, restituisci il richiesto e speriamo bene
        logger.error("Nessun modello disponibile, tentativo con modello richiesto")
        return model

    def _execute_with_retry(self, operation, *args, **kwargs):
        """Esegue un'operazione con retry automatico."""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return operation(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"Tentativo {attempt + 1} fallito: {e}. Riprovo tra {wait_time}s")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Tutti i {self.max_retries} tentativi falliti")
        
        # Se arriviamo qui, tutti i tentativi sono falliti
        if last_exception:
            raise last_exception

    def call(
        self,
        prompt: str,
        model: Optional[ModelName] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.8
    ) -> str:
        """
        Esegue una chiamata bloccante a un modello LLM con retry automatico.
        """
        target_model = self._validate_model(model if model else self.default_model)
        logger.info(f"Chiamata bloccante al modello: {target_model}")

        def _call_operation():
            messages = [{'role': 'user', 'content': prompt}]
            if system_prompt:
                messages.insert(0, {'role': 'system', 'content': system_prompt})

            response = ollama.chat(
                model=target_model,
                messages=messages,
                options={'temperature': temperature}
            )
            return response['message']['content']

        try:
            return self._execute_with_retry(_call_operation)
        except Exception as e:
            logger.error(f"[Errore Chiamata] Modello: {target_model} | {e}")
            return ""

    def stream(
        self,
        prompt: str,
        model: Optional[ModelName] = "deepseek-r1:8b",
        system_prompt: Optional[str] = None,
        print_live: bool = True
    ) -> Iterator[str]:
        """
        Esegue una chiamata in streaming a un modello LLM, restituendo i chunk di testo.
        Se print_live è True, stampa i chunk direttamente in shell.
        """
        target_model = model if model else self.default_model
        logger.info(f"Avvio streaming dal modello: {target_model}")

        messages = [{'role': 'user', 'content': prompt}]
        if system_prompt:
            messages.insert(0, {'role': 'system', 'content': system_prompt})

        full_response_content = "" 
        try:
            stream = ollama.chat(
                model=target_model,
                messages=messages,
                stream=True
            )
            for chunk_data in stream: # Renamed to avoid conflict with 'chunk' variable
                chunk = chunk_data['message']['content']
                if print_live:
                    print(chunk, end="", flush=True) # Stampa il chunk direttamente in shell
                full_response_content += chunk # Accumula il contenuto
                yield chunk # Restituisce il chunk al chiamante
        except Exception as e:
            logger.error(f"[Errore Streaming] Modello: {target_model} | {e}")
            yield "" # Assicurati di yieldare una stringa vuota per mantenere l'iteratore
        finally:
            # Qui potresti aggiungere un log del contenuto completo dello stream se utile,
            # ma lo faremo nella pipeline per il "reasoning" specifico.
            pass
    
    def call_with_context(
        self,
        prompt: str,
        context: AgentContext,
        model: Optional[ModelName] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.8,
        max_history_turns: int = 10
    ) -> str:
        """
        Esegue una chiamata bloccante a un modello LLM includendo la cronologia della conversazione.
        """
        target_model = model if model else self.default_model
        logger.info(f"Chiamata con contesto al modello: {target_model}")

        # Costruisci i messaggi includendo la cronologia
        messages = []
        
        # Aggiungi prompt di sistema se presente
        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})
        
        # Aggiungi cronologia conversazione (limitata agli ultimi max_history_turns)
        if context.conversation_history:
            recent_history = context.conversation_history[-max_history_turns:]
            for role, content in recent_history:
                if role in ['user', 'assistant'] and content.strip():
                    # Mappa i ruoli per Ollama
                    ollama_role = 'assistant' if role == 'assistant' else 'user'
                    messages.append({'role': ollama_role, 'content': content})
        
        # Aggiungi il prompt corrente
        messages.append({'role': 'user', 'content': prompt})
        
        # Log della cronologia utilizzata
        logger.debug(f"Utilizzo {len(messages)} messaggi nella conversazione (incluso prompt corrente)")
        
        try:
            response = ollama.chat(
                model=target_model,
                messages=messages,
                options={'temperature': temperature}
            )
            return response['message']['content']
        except Exception as e:
            logger.error(f"[Errore Chiamata con Contesto] Modello: {target_model} | {e}")
            return ""

    def stream_with_context(
        self,
        prompt: str,
        context: AgentContext,
        model: Optional[ModelName] = None,
        system_prompt: Optional[str] = None,
        print_live: bool = True,
        max_history_turns: int = 10
    ) -> Iterator[str]:
        """
        Esegue una chiamata in streaming a un modello LLM includendo la cronologia della conversazione.
        """
        target_model = model if model else self.default_model
        logger.info(f"Avvio streaming con contesto dal modello: {target_model}")

        # Costruisci i messaggi includendo la cronologia
        messages = []
        
        # Aggiungi prompt di sistema se presente
        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})
        
        # Aggiungi cronologia conversazione (limitata agli ultimi max_history_turns)
        if context.conversation_history:
            recent_history = context.conversation_history[-max_history_turns:]
            for role, content in recent_history:
                if role in ['user', 'assistant'] and content.strip():
                    # Mappa i ruoli per Ollama
                    ollama_role = 'assistant' if role == 'assistant' else 'user'
                    messages.append({'role': ollama_role, 'content': content})
        
        # Aggiungi il prompt corrente
        messages.append({'role': 'user', 'content': prompt})
        
        # Log della cronologia utilizzata
        logger.debug(f"Utilizzo {len(messages)} messaggi nella conversazione streaming (incluso prompt corrente)")
        
        try:
            stream = ollama.chat(
                model=target_model,
                messages=messages,
                stream=True
            )
            for chunk_data in stream:
                chunk = chunk_data['message']['content']
                if print_live:
                    print(chunk, end="", flush=True)
                yield chunk
        except Exception as e:
            logger.error(f"[Errore Streaming con Contesto] Modello: {target_model} | {e}")
            yield ""

    def call_json(
        self,
        prompt: str,
        model: Optional[str] = None, # Modificato ModelName a str per uso generico
        # PROMPT DI SISTEMA PIÙ FORTE E TRADOTTO
        system_prompt: str = "You must respond exclusively with a valid JSON array, with absolutely no additional text, explanations, preambles, or formatting. Your response must begin immediately with '[' and end immediately with ']'. Do not include markdown blocks ('```json')."
    ) -> Optional[List[Dict[str, Any]]]: # Modificato tipo di ritorno a List[Dict] come previsto
        """
        Esegue una chiamata a un LLM forzando l'output in formato JSON.
        Restituisce un array JSON (List[Dict]) o None in caso di errore.
        """
        target_model = model if model else self.default_model
        logger.info(f"Chiamata JSON al modello: {target_model}")

        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': prompt}
        ]
        
        try:
            response = ollama.chat(
                model=target_model,
                messages=messages,
                format='json' 
            )
            
            raw_content = response['message']['content']
            
            # Post-processing: Rimuovi prefissi/suffissi problematici noti (reasoning deepseek)
            json_string = raw_content.strip()
            
            # Tenta di rimuovere i blocchi markdown comuni e i blocchi di ragionamento dell'LLM
            if json_string.startswith("```json"):
                json_string = json_string[len("```json"):].strip()
            if json_string.endswith("```"):
                json_string = json_string[:-len("```")].strip()
            
            # Rimuovi aggressivamente qualsiasi potenziale blocco <think>
            json_string = json_string.split("</think>")[-1].strip() 

            if json_string.startswith("{") and json_string.endswith("}"):
                # Singolo oggetto → wrappalo in lista
                return [json.loads(json_string)]

            start_index = json_string.find('[')
            end_index = json_string.rfind(']')

            if start_index == -1 or end_index == -1:
                raise json.JSONDecodeError("Non è stato possibile trovare un array JSON valido nell'output del modello.", json_string, 0)

            clean_json_string = json_string[start_index : end_index + 1]
            return json.loads(clean_json_string)
        except json.JSONDecodeError as e:
            truncated = raw_content[:1000] if isinstance(raw_content, str) else str(raw_content)
            logger.error(
                f"[Errore Decodifica JSON] Il modello non ha restituito un JSON valido. Errore: {e}. Output: '{truncated}'"
            )
            return None
        except Exception as e:
            logger.error(f"[Errore Chiamata JSON] Modello: {target_model} | {e}")
            return None

    def manage_conversation_context(
        self,
        context: AgentContext,
        max_tokens_estimate: int = 4000,
        max_turns: int = 20
    ) -> None:
        """
        Gestisce automaticamente la cronologia della conversazione per evitare
        di superare i limiti di token del modello.
        """
        if not context.conversation_history:
            return
        
        # Stima approssimativa: 1 token ≈ 4 caratteri
        total_chars = sum(len(content) for _, content in context.conversation_history)
        estimated_tokens = total_chars // 4
        
        # Se superiamo i limiti, riduci la cronologia
        if estimated_tokens > max_tokens_estimate or len(context.conversation_history) > max_turns:
            # Mantieni solo le conversazioni più recenti
            if len(context.conversation_history) > max_turns:
                context.conversation_history = context.conversation_history[-max_turns:]
                logger.info(f"Ridotta cronologia conversazione a {max_turns} turni")
            
            # Se ancora troppo grande, riduci ulteriormente
            while len(context.conversation_history) > 5:
                total_chars = sum(len(content) for _, content in context.conversation_history)
                if total_chars // 4 <= max_tokens_estimate:
                    break
                context.conversation_history.pop(0)  # Rimuovi il più vecchio
            
            if len(context.conversation_history) != len(context.conversation_history):
                logger.info("Ridotta cronologia conversazione per rispettare i limiti di token")

    def add_to_conversation_history(
        self,
        context: AgentContext,
        role: str,
        content: str,
        auto_manage: bool = True
    ) -> None:
        """
        Aggiunge un messaggio alla cronologia della conversazione e opzionalmente
        gestisce automaticamente i limiti.
        """
        if content and content.strip():
            context.conversation_history.append((role, content.strip()))
            
            if auto_manage:
                self.manage_conversation_context(context)
            
            logger.debug(f"Aggiunto alla cronologia: {role}={content[:50]}...")

    def get_conversation_summary(self, context: AgentContext) -> str:
        """
        Genera un riassunto della conversazione corrente per debugging o logging.
        """
        if not context.conversation_history:
            return "Nessuna cronologia conversazione"
        
        summary_parts = []
        for i, (role, content) in enumerate(context.conversation_history[-5:]):  # Ultimi 5 messaggi
            content_preview = content[:100] + "..." if len(content) > 100 else content
            summary_parts.append(f"{i+1}. {role}: {content_preview}")
        
        return "\n".join(summary_parts)

    # --- Esempio di Utilizzo del Nuovo Client ---

if __name__ == "__main__":
    try:
        client = LLMClient(default_model="deepseek-r1:8b")

        print("\n--- Chiamata Semplice ---")
        risposta = client.call("Spiegami in una frase cos'è un buco nero.")
        print(f"Risposta del modello: {risposta}")

        print("\n--- Chiamata in Streaming (con stampa live) ---")
        prompt_stream = "Racconta una breve storia su un robot che scopre la musica."
        # Passa print_live=True per vedere lo stream in tempo reale
        full_story_chunks = []
        for chunk in client.stream(prompt_stream, model="mistral", print_live=True):
            full_story_chunks.append(chunk)
        full_story = "".join(full_story_chunks)
        print("\n\n--- Fine Streaming ---")
        # Puoi anche stampare la storia completa dal full_story qui se necessario
        # print(f"Storia completa: {full_story}")

        print("\n--- Chiamata con Output JSON Garantito ---")
        prompt_json = "Estrai le informazioni dall'email: 'Ciao, sono Mario, la versione del kf3 3.4.2 non funziona. Non riesco a scrivere correttamente i FIR?' Estrai nome, software, e bug."
        dati_estratti = client.call_json(prompt_json, model="llama3:8b-instruct")
        
        if dati_estratti:
            print("Dati estratti con successo:")
            print(json.dumps(dati_estratti, indent=4))
        else:
            print("Estrazione JSON fallita.")

    except Exception as e:
        logger.critical(f"Esecuzione fallita. Controlla che Ollama sia attivo. Errore: {e}")