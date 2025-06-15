# Wiki di Kchat

Questa wiki descrive in dettaglio l'architettura e le principali funzioni del progetto **Kchat**, un chatbot agentico pensato per l'esecuzione locale e senza dipendenze da servizi cloud.

## Indice

- [Panoramica generale](#panoramica-generale)
- [Agenti principali](#agenti-principali)
- [Moduli di utilità](#moduli-di-utilità)
- [Strumenti di categorizzazione](#strumenti-di-categorizzazione)
- [Esecuzione da riga di comando](#esecuzione-da-riga-di-comando)

## Panoramica generale

Il bot opera tramite una catena di agenti specializzati che condividono lo stesso contesto (`AgentContext`). Ogni agente legge i campi rilevanti del contesto, ne aggiorna altri e registra la propria attività nei file di log. Gli agenti sono coordinati da `OrchestratorAgent` che decide di volta in volta quali passi eseguire.

Il contesto (`agents/context.py`) definisce i campi di memoria condivisa:

```python
@dataclass
class AgentContext:
    user_id: str
    session_id: str
    input: str
    role: str = "user"
    language: str = "en"
    intent: Optional[str] = None
    confidence: Optional[float] = None
    documents: List[Any] = field(default_factory=list)
    response: Optional[str] = None
    clarification_attempted: bool = False
    formality: Optional[str] = None
    mixed_language: bool = False
    reasoning_trace: str = ""
    source_reliability: float = 0.0
    error_flag: bool = False
    conversation_history: List[Tuple[str, str]] = field(default_factory=list)
```

Tutte le chiamate agli agenti ricevono e restituiscono un `AgentContext` aggiornato.

## Agenti principali

### `action_agent.py`
- **`run(context)`**: segnaposto per l'esecuzione di azioni di backend. Imposta `source_reliability` e registra l'esecuzione nel log `action_log`.

### `clarification_agent.py`
- **`_most_common_question()`**: esamina lo storico dei log per individuare la domanda di chiarimento più frequente.
- **`run(context)`**: genera una domanda di chiarimento sfruttando `generate_contextual_question` o in fallback `generate_fallback_question`. Aggiorna `context.response` e marca `clarification_attempted`.

### `document_retriever_agent.py`
- **`_embed(text)`**: produce un vettore numerico deterministico usato come embedding.
- **`_retrieve(query, role)`**: esegue la ricerca nella collezione Qdrant e filtra i risultati in base al ruolo dell'utente.
- **`run(context, query=None)`**: recupera i documenti pertinenti, applica controlli sui permessi e aggiorna `context.documents`.

### `embedding_ingestor_agent.py`
- **`run(context, path, metadata=None)`**: legge un file, suddivide il testo in chunk e calcola embedding fittizi, registrando le informazioni nel log `ingest_log`.

### `intent_agent.py`
- **`_rule_based_intent(text)`**: tenta una classificazione rapida tramite parole chiave.
- **`_most_frequent_from_logs()`**: ritorna l'intento più ricorrente nei log precedenti.
- **`run(context)`**: unisce la stima rule‑based con quella tramite LLM (`detect_intent`); aggiorna `intent`, `confidence` e `source_reliability`.

### `language_agent.py`
- **`speech_to_text(audio_path)`**: placeholder per trascrizione vocale.
- **`_detect_formality(text)`**: determina il registro (formale/informale) in base a determinate parole chiave.
- **`_mixed_language(text)`**: rileva la presenza di più lingue nello stesso input.
- **`run(context)`**: usa `detect_language` per impostare `language`, valuta la formalità e segna se l'input contiene lingue miste.

### `orchestrator_agent.py`
- **`_fallback_sequence(context)`**: in caso di errore di orchestrazione, restituisce una sequenza di agenti predefinita e aggiorna il campo `reasoning_trace`.
- **`choose_agent_sequence(context)`**: sfrutta `call_mistral` per decidere dinamicamente la sequenza di agenti da lanciare. In caso di problemi utilizza `_fallback_sequence`.
- **`run(context)`**: aggiunge il messaggio corrente allo storico, esegue gli agenti scelti, verifica la risposta e la traduce nella lingua finale.

### `quotation_agent.py`
- **`run(context)`**: esempio minimale di generazione di un preventivo (PDF); aggiorna `response` e `source_reliability`.

### `response_agent.py`
- **`run(context)`**: genera la risposta finale scegliendo tre modalità: basata su documenti, su azioni di backend oppure puro small talk tramite `openchat_worker.generate_response`.

### `supervisor_agent.py`
- **`_analyze_intent_log(text)`** / **`_analyze_validation_log(text)`**: analisi basilare dei log per suggerire miglioramenti.
- **`_collect_snippets()`**: raccoglie estratti dei log più recenti.
- **`run(context)`**: invoca Mistral per produrre raccomandazioni oppure usa analisi locale in fallback.

### `translation_agent.py`
- **`_auto_correct(text)`**: piccola correzione ortografica prima di tradurre.
- **`run(context, target_lang, style="neutral")`**: traduce `context.response` (o l'input se non presente) nella lingua indicata, opzionalmente applicando uno stile.

### `verification_agent.py`
- **`run(context)`**: valida la risposta chiamando `verify_response` più volte. Registra il risultato (valid/invalid/uncertain) e imposta `error_flag` se necessario.

## Moduli di utilità

### `language_detector.py`
- **`detect_language(user_input)`**: sfrutta Mistral per riconoscere la lingua del testo restituendo un codice ISO 639‑1.

### `translator.py`
- **`translate(text, target_lang)`**: effettua la traduzione completa usando Mistral.
- **`translate_stream(text, target_lang)`**: versione che restituisce un iteratore di token tradotti.

### `openchat_worker.py`
- **`generate_response(user_input, intent, lang)`**: chiama OpenChat via Ollama per ottenere una risposta testuale.
- **`generate_response_stream(user_input, intent, lang)`**: equivalente ma in modalità streaming.

### `verifier.py`
- **`verify_response(user_input, response)`**: chiede a Mistral di valutare se la risposta è pertinente; ritorna `True`/`False`.

### `file_classifier.py`
- **`main()`**: utility CLI per classificare file in una cartella o archivio ZIP sfruttando la classe `Categorizer`.
- Salva il risultato in `output.json`; se la categoria impostata è `product_price`, il file viene creato o aggiornato in `prices.json`.

### `csv_utils.py`
- **`load_csv(path)`**: carica file CSV di struttura variabile usando Pandas restituendo una lista di dizionari.
- **`summarize_csv(path)`**: impiega `call_mistral` per riassumere in una frase il significato delle colonne.

## Strumenti di categorizzazione

Il pacchetto `categorizer/` fornisce strumenti per catalogare documenti:

- **`categorizer.py`**: classe `Categorizer` con `process_file()` e `run()` per analizzare file, estrarre testo, categorie e metadati.
- **`classifier.py`**: funzioni `score()`, `extract_subcategories()` e `classify()` per una prima classificazione basata su parole chiave ed entità.
- **`entity_extractor.py`**: `extract_entities()` estrae nomi di prodotti tramite spaCy.
- **`extractor.py`**: `extract_text()` apre PDF, DOCX, XLSX, HTML e TXT restituendo il testo estratto con log degli errori.
- **`scanner.py`**: `scan()` restituisce l'elenco di file supportati presenti in una cartella o in un archivio ZIP.
- **`validator.py`**: funzione `confirm()` che permette la validazione interattiva o tramite LLM del risultato della classificazione.

## Esecuzione da riga di comando

Per avviare una sessione interattiva del bot:

```bash
python main.py
```

Per classificare documenti in automatico:

```bash
python file_classifier.py <cartella_o_zip> \
  --category tech_assistance --mode auto
```

Le categorie valide sono `tech_assistance`, `software_assistance`,
`product_price` e `product_guide`.

È inoltre possibile avviare un piccolo server REST:

```bash
uvicorn file_classifier:app --reload
```

ed effettuare una richiesta POST a `/classify` specificando `input_path` e
`category` nel corpo JSON.

La cartella `tests/` contiene suite PyTest che coprono le funzioni principali. Prima di mettere in produzione il progetto è consigliato eseguire:

```bash
ruff .
mypy .
pytest
```

In questo modo si verificano lo stile del codice, la coerenza dei tipi e il corretto funzionamento dei test.

