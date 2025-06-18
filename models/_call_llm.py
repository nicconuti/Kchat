try:
    import ollama
except ImportError:  # Provide a minimal stub so other modules can run
    class _OllamaStub:
        def ps(self):
            logger = logging.getLogger(__name__)
            logger.warning("Ollama package not available; using stub client")

        def chat(self, *args, **kwargs):
            if kwargs.get("stream"):
                # yield a single empty chunk to satisfy streaming interface
                yield {"message": {"content": ""}}
            return {"message": {"content": ""}}

    ollama = _OllamaStub()
import logging
import json
from typing import Iterator, Literal, Dict, Any, Optional, List

# --- Configurazione e Tipi ---

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

ModelName = Literal[
    "mistral",
    "openchat",
    "deepseek-r1:8b",       # Versione standard
    "deepseek-r1:14b",    # Versione più potente
    "llama3:8b-instruct"
]


# --- Classe Client per Ollama ---

class LLMClient:
    """
    Un client robusto per interagire con i modelli locali di Ollama.
    Centralizza la logica di chiamata, streaming e gestione degli errori.
    """
    def __init__(self, default_model: ModelName = "mistral"):
        self.default_model = default_model
        try:
            # Verifica la connessione con Ollama all'avvio
            ollama.ps()
            logger.info("Connessione con Ollama stabilita con successo.")
        except Exception as e:
            logger.error(f"Impossibile connettersi a Ollama. Assicurati che sia in esecuzione. Errore: {e}")
            raise

    def call(
        self,
        prompt: str,
        model: Optional[ModelName] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.8
    ) -> str:
        """
        Esegue una chiamata bloccante a un modello LLM.
        """
        target_model = model if model else self.default_model
        logger.info(f"Chiamata bloccante al modello: {target_model}")

        messages = [{'role': 'user', 'content': prompt}]
        if system_prompt:
            messages.insert(0, {'role': 'system', 'content': system_prompt})

        try:
            response = ollama.chat(
                model=target_model,
                messages=messages,
                options={'temperature': temperature}
            )
            return response['message']['content']
        except Exception as e:
            logger.error(f"[Errore Chiamata] Modello: {target_model} | {e}")
            return ""

    def stream(
        self,
        prompt: str,
        model: Optional[ModelName] = None,
        system_prompt: Optional[str] = None,
        # Aggiungi un parametro per controllare la stampa live
        print_live: bool = False
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

        full_response_content = "" # Aggiunto per accumulare la risposta completa
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

            # Trova il primo '[' e l'ultimo ']' per estrarre l'array JSON puro
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
        prompt_json = "Estrai le informazioni dall'email: 'Ciao, sono Mario Rossi, il mio ordine è #A42-B7. Potete spedirlo a Firenze?' Estrai nome, numero ordine e città."
        dati_estratti = client.call_json(prompt_json, model="llama3:8b-instruct")
        
        if dati_estratti:
            print("Dati estratti con successo:")
            print(json.dumps(dati_estratti, indent=4))
        else:
            print("Estrazione JSON fallita.")

    except Exception as e:
        logger.critical(f"Esecuzione fallita. Controlla che Ollama sia attivo. Errore: {e}")