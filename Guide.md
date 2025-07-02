# Guida Completa a Kchat

## 📋 Indice
- [Panoramica del Sistema](#panoramica-del-sistema)
- [Installazione e Configurazione](#installazione-e-configurazione)
- [Architettura del Sistema](#architettura-del-sistema)
- [Funzionalità Principali](#funzionalità-principali)
- [Guida all'Uso](#guida-alluso)
- [Deployment in Produzione](#deployment-in-produzione)
- [Monitoraggio e Manutenzione](#monitoraggio-e-manutenzione)
- [Risoluzione Problemi](#risoluzione-problemi)

---

## 🎯 Panoramica del Sistema

Kchat è un sistema di chatbot agenziale avanzato progettato per l'assistenza clienti automatizzata. Utilizza modelli LLM locali (Ollama) e un'architettura multi-agente per fornire risposte intelligenti e contestuali.

### Caratteristiche Principali
- **Sistema Multi-Agente**: Orchestrazione intelligente di agenti specializzati
- **Integrazione LLM Locale**: Supporto per Ollama (deepseek-r1:14b, mistral, openchat)
- **Database Vettoriale**: Integrazione con Qdrant per ricerca semantica
- **Generazione PDF**: Creazione automatica di preventivi professionali
- **Sistema di Backend**: Gestione ticket, appuntamenti e reclami
- **Containerizzazione**: Deployment completo con Docker e Docker Compose

---

## 🚀 Installazione e Configurazione

### Prerequisiti
- Python 3.9+ 
- Docker e Docker Compose (per deployment containerizzato)
- Ollama installato e configurato
- Qdrant (opzionale, per database vettoriale)

### Installazione Rapida con Docker

```bash
# 1. Clona il repository
git clone <repository-url>
cd Kchat

# 2. Avvia l'ambiente di produzione
./docker/start.sh prod

# 3. Per sviluppo
./docker/start.sh dev

# 4. Per eseguire i test
./docker/start.sh test
```

### Installazione Manuale

```bash
# 1. Installa le dipendenze
pip install -r requirements.txt

# 2. Configura le variabili d'ambiente
cp .env.example .env
# Modifica .env secondo le tue necessità

# 3. Avvia Ollama
ollama serve

# 4. Scarica i modelli necessari
ollama pull deepseek-r1:14b
ollama pull mistral
ollama pull openchat

# 5. Avvia l'applicazione
python main.py
```

### Configurazione Avanzata

Crea un file `.env` per personalizzare la configurazione:

```env
# Configurazione Ollama
OLLAMA_HOST=localhost
OLLAMA_PORT=11434

# Configurazione Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Configurazione Logging
LOG_LEVEL=INFO
LOG_FILE=logs/kchat.log

# Configurazione Backend
BACKEND_DATA_DIR=backend_data
EMBEDDINGS_DIR=embeddings
QUOTES_DIR=quotes
```

---

## 🏗️ Architettura del Sistema

### Componenti Principali

```
Kchat/
├── agents/                    # Agenti specializzati
│   ├── orchestrator_agent.py  # Orchestrazione principale
│   ├── intent_agent.py        # Rilevamento intenzioni
│   ├── clarification_agent.py # Richieste di chiarimento
│   ├── document_retriever_agent.py # Ricerca documenti
│   ├── quotation_agent.py     # Generazione preventivi
│   ├── action_agent.py        # Azioni backend
│   └── embedding_ingestor_agent.py # Gestione embeddings
├── models/                    # Interfacce LLM
│   ├── _call_llm.py          # Client LLM principale
│   └── call_local_llm.py     # Chiamate Ollama
├── knowledge_pipeline/        # Pipeline di conoscenza
├── utils/                     # Utilità generali
├── tests/                     # Suite di test
└── docker/                    # Configurazioni Docker
```

### Flusso di Elaborazione

1. **Input Utente** → Ricevuto dal sistema principale
2. **Rilevamento Intenzioni** → Classificazione automatica dell'input
3. **Orchestrazione** → Selezione e coordinamento degli agenti appropriati
4. **Elaborazione Specializzata** → Esecuzione da parte degli agenti specifici
5. **Generazione Risposta** → Compilazione della risposta finale
6. **Output Strutturato** → Consegna all'utente con metadati

### Agenti Specializzati

#### 🎯 **Orchestrator Agent**
- Coordina l'intero flusso di elaborazione
- Gestisce il recovery degli errori
- Mantiene la coerenza del contesto

#### 🧠 **Intent Agent** 
- Classifica le intenzioni dell'utente
- Supporta rilevamento multilingue
- Gestisce casi ambigui

#### 📄 **Document Retriever Agent**
- Ricerca semantica nei documenti
- Integrazione con Qdrant
- Fallback su storage locale

#### 💰 **Quotation Agent**
- Genera preventivi PDF professionali
- Estrazione automatica prodotti/servizi
- Template personalizzabili

#### ⚙️ **Action Agent**
- Gestisce azioni backend (ticket, appuntamenti, reclami)
- Storage JSON strutturato
- Validazione dati automatica

---

## 🔧 Funzionalità Principali

### 1. Generazione Preventivi PDF

Il sistema genera automaticamente preventivi professionali in formato PDF:

```python
# Esempio di utilizzo
from agents.quotation_agent import run
from agents.context import AgentContext

context = AgentContext(
    user_id="cliente123",
    session_id="sessione456", 
    input="Vorrei un preventivo per servizi di consulenza IT"
)

result = run(context)
# PDF generato in quotes/quote_YYYYMMDD_HHMMSS.pdf
```

**Caratteristiche PDF:**
- Header professionale con logo e informazioni aziendali
- Dettagli cliente e sessione
- Tabella prodotti/servizi con prezzi
- Calcolo automatico totali e IVA
- Footer con termini e condizioni

### 2. Sistema di Backend Azioni

Gestione completa di ticket, appuntamenti e reclami:

```python
# Creazione ticket
context.input = "Ho un problema con il servizio X"
action_context = action_agent.run(context)

# Prenotazione appuntamento  
context.input = "Vorrei prenotare un appuntamento per martedì"
action_context = action_agent.run(context)

# Gestione reclami
context.input = "Voglio fare un reclamo per il servizio Y"
action_context = action_agent.run(context)
```

**Storage Strutturato:**
- `backend_data/tickets/` - Ticket di assistenza
- `backend_data/appointments/` - Appuntamenti programmati
- `backend_data/complaints/` - Reclami clienti
- Formato JSON con metadati completi

### 3. Ricerca Semantica Documenti

Sistema avanzato di ricerca basato su embeddings:

```python
# Ricerca automatica documenti
context.input = "Informazioni sui prezzi dei servizi cloud"
doc_context = document_retriever_agent.run(context)

# Risultati con punteggi di similarità
for doc in doc_context.documents:
    print(f"Documento: {doc['path']}")
    print(f"Score: {doc['score']}")
    print(f"Contenuto: {doc['content'][:200]}...")
```

**Caratteristiche:**
- Embeddings con sentence-transformers
- Integrazione Qdrant per performance
- Fallback su storage locale
- Chunking semantico intelligente

### 4. Gestione Conversazioni

Sistema completo di gestione del contesto conversazionale:

```python
# Chiamata con contesto
from models._call_llm import LLMClient

client = LLMClient()
response = client.call_with_context(
    prompt="Come posso aiutarti oggi?",
    context_messages=conversation_history,
    model="deepseek-r1:14b"
)

# Gestione automatica della cronologia
client.add_to_conversation_history("user", "Ciao, ho bisogno di aiuto")
client.add_to_conversation_history("assistant", "Certo! Come posso aiutarti?")
```

---

## 📚 Guida all'Uso

### Interazione Base

```bash
# Avvio dell'applicazione
python main.py

# Esempi di interazioni
💬 Kchat
Ciao! Come posso aiutarti oggi?

Utente: "Vorrei informazioni sui vostri servizi"
Kchat: [Ricerca documenti e fornisce informazioni dettagliate]

Utente: "Quanto costa il servizio di consulenza?"
Kchat: [Genera preventivo automatico]

Utente: "Ho un problema tecnico"
Kchat: [Crea ticket di assistenza]

Utente: "Vorrei prenotare un appuntamento"
Kchat: [Gestisce prenotazione appuntamento]
```

### Tipi di Richieste Supportate

#### 🔍 **Richieste Informative**
- "Che servizi offrite?"
- "Quali sono i vostri orari?"
- "Come funziona il vostro processo?"

#### 💰 **Richieste di Preventivo**
- "Quanto costa il servizio X?"
- "Vorrei un preventivo per..."
- "Prezzi per consulenza IT"

#### 🎫 **Supporto Tecnico**
- "Ho un problema con..."
- "Il servizio non funziona"
- "Errore nell'applicazione"

#### 📅 **Prenotazioni**
- "Vorrei prenotare un appuntamento"
- "Disponibilità per la prossima settimana"
- "Posso cambiare l'appuntamento?"

#### 📢 **Reclami**
- "Voglio fare un reclamo"
- "Non sono soddisfatto del servizio"
- "Problema con la fatturazione"

### Comandi Speciali

- `exit` - Chiude l'applicazione
- `help` - Mostra informazioni di aiuto
- `clear` - Pulisce la cronologia conversazione

---

## 🚀 Deployment in Produzione

### Deployment con Docker Compose

```yaml
# docker-compose.yml configurazione produzione
version: '3.8'

services:
  kchat:
    image: kchat:latest
    environment:
      - OLLAMA_HOST=ollama
      - QDRANT_HOST=qdrant
    depends_on:
      - qdrant
      - ollama
    volumes:
      - ./logs:/app/logs
      - ./backend_data:/app/backend_data
    ports:
      - "8000:8000"

  qdrant:
    image: qdrant/qdrant:v1.7.4
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama

volumes:
  qdrant_data:
  ollama_data:
```

### Script di Avvio Automatico

```bash
#!/bin/bash
# docker/start.sh

set -e

ENVIRONMENT=${1:-dev}

case $ENVIRONMENT in
  "prod")
    echo "🚀 Avvio ambiente di produzione..."
    docker-compose --profile production up -d
    ;;
  "dev")
    echo "🔧 Avvio ambiente di sviluppo..."
    docker-compose --profile development up -d
    ;;
  "test")
    echo "🧪 Esecuzione test..."
    docker-compose run --rm kchat-test
    ;;
  *)
    echo "Uso: $0 {prod|dev|test}"
    exit 1
    ;;
esac

echo "✅ Ambiente $ENVIRONMENT avviato con successo!"
```

### Health Checks

Il sistema include health checks automatici:

```python
# docker/health-check.py
def check_system_health():
    checks = [
        ("Python environment", check_python_environment),
        ("File system", check_file_system), 
        ("Agent context", check_agent_context),
        ("LLM client", check_llm_client)
    ]
    # Esegue tutti i controlli di salute
```

### CI/CD Pipeline

Pipeline automatica con GitHub Actions:

```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.9', '3.10', '3.11']
    
  docker:
    runs-on: ubuntu-latest
    steps:
      - name: Build and test Docker images
        run: |
          docker build --target testing -t kchat:test .
          docker run --rm kchat:test
```

---

## 📊 Monitoraggio e Manutenzione

### Sistema di Logging

```python
# Configurazione logging centralizzato
import logging
from utils.logger import get_logger

logger = get_logger("kchat_main")

# Livelli di log supportati
logger.debug("Informazioni di debug dettagliate")
logger.info("Operazioni normali del sistema")
logger.warning("Situazioni che richiedono attenzione")
logger.error("Errori che non fermano l'esecuzione")
logger.critical("Errori critici che fermano il sistema")
```

### Metriche di Sistema

Il sistema traccia automaticamente:

- **Performance**: Tempi di risposta degli agenti
- **Qualità**: Punteggi di confidenza e affidabilità
- **Utilizzo**: Statistiche chiamate LLM e ricerche
- **Errori**: Categorie e frequenze degli errori

### Backup e Recovery

```bash
# Script di backup automatico
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backups/backup_$DATE"

mkdir -p $BACKUP_DIR

# Backup dati backend
cp -r backend_data/ $BACKUP_DIR/
cp -r embeddings/ $BACKUP_DIR/
cp -r quotes/ $BACKUP_DIR/
cp -r logs/ $BACKUP_DIR/

echo "✅ Backup completato in $BACKUP_DIR"
```

### Manutenzione Periodica

**Giornaliera:**
- Verifica health checks
- Rotazione log files
- Monitoraggio spazio disco

**Settimanale:**
- Backup completo dati
- Analisi performance
- Aggiornamento modelli LLM

**Mensile:**
- Ottimizzazione database vettoriale
- Pulizia file temporanei
- Review sicurezza sistema

---

## 🔧 Risoluzione Problemi

### Problemi Comuni

#### 1. **Ollama Non Raggiungibile**
```bash
# Sintomi: Errori di connessione LLM
# Soluzione:
ollama serve
# oppure
docker-compose restart ollama
```

#### 2. **Qdrant Non Disponibile**
```bash
# Sintomi: Fallback a storage locale
# Soluzione:
docker-compose restart qdrant
# Verifica: curl http://localhost:6333/health
```

#### 3. **Errori di Memoria**
```bash
# Sintomi: Out of memory durante embeddings
# Soluzione: Aumenta memoria Docker o usa batch più piccoli
# docker-compose.yml:
services:
  kchat:
    deploy:
      resources:
        limits:
          memory: 4G
```

#### 4. **Performance Lente**
```bash
# Controllo modelli caricati
ollama list

# Ottimizzazione Qdrant
# Aumenta parametri di cache nel config
```

### Debug Avanzato

#### Modalità Debug
```bash
# Avvio con logging debug
export LOG_LEVEL=DEBUG
python main.py

# Log dettagliati in logs/kchat.log
tail -f logs/kchat.log
```

#### Test Componenti Individuali
```bash
# Test singoli agenti
pytest tests/test_intent_router.py -v
pytest tests/test_document_retriever_agent.py -v

# Test integrazione
pytest tests/ -k "integration" -v
```

#### Monitoraggio Real-time
```bash
# Monitoraggio container
docker stats

# Log in tempo reale
docker-compose logs -f kchat

# Health check manuale
python docker/health-check.py
```

### Log di Errori Frequenti

| Errore | Causa | Soluzione |
|--------|-------|-----------|
| `Connection refused localhost:11434` | Ollama non avviato | `ollama serve` |
| `No module named 'sentence_transformers'` | Dipendenze mancanti | `pip install -r requirements.txt` |
| `Qdrant connection timeout` | Qdrant non disponibile | Riavvia servizio Qdrant |
| `PDF generation failed` | ReportLab non installato | `pip install reportlab` |
| `Permission denied backend_data/` | Permessi directory | `chmod 755 backend_data/` |

---

## 📞 Supporto e Contributi

### Documentazione Aggiuntiva
- `CLAUDE.md` - Guida tecnica per sviluppatori
- `todolist.md` - Storia completa dello sviluppo
- `README.md` - Informazioni base del progetto

### Struttura per Contributi
1. Fork del repository
2. Creazione branch feature (`git checkout -b feature/nuova-funzionalita`)
3. Commit delle modifiche (`git commit -am 'Aggiunge nuova funzionalità'`)
4. Push del branch (`git push origin feature/nuova-funzionalita`)
5. Creazione Pull Request

### Test Prima dei Contributi
```bash
# Esegui tutti i test
pytest tests/ -v

# Verifica stile codice
ruff check .
black --check .

# Type checking
mypy . --ignore-missing-imports
```

---

## 🎉 Conclusione

Kchat rappresenta un sistema completo e production-ready per l'assistenza clienti automatizzata. Con la sua architettura modulare, integrazione LLM avanzata e capacità di deployment scalabile, offre una soluzione robusta per aziende di qualsiasi dimensione.

Il sistema è stato progettato con focus su:
- **Facilità d'uso** per utenti finali
- **Flessibilità** per sviluppatori  
- **Scalabilità** per crescita aziendale
- **Affidabilità** per uso in produzione

Per domande specifiche o supporto tecnico, consultare la documentazione tecnica in `CLAUDE.md` o aprire una issue nel repository del progetto.

---

*Documentazione aggiornata al: Luglio 2025*
*Versione Kchat: 1.0.0 Production Ready*