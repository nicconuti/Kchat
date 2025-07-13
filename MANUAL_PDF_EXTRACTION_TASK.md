# Manual PDF Extraction Task - Processo di Estrazione Manuale di Qualità Superiore

## Obiettivo
Estrarre manualmente ogni PDF della directory `data/user_guides` per creare JSON di qualità superiore rispetto a quelli esistenti in `data/`, garantendo massima affidabilità e completezza per il sistema RAG.

## Workflow Dettagliato

### 1. SELEZIONE PDF
- **Input**: Directory `data/user_guides/` e `data/user_guides/old/`
- **Azione**: Selezionare il primo PDF non ancora processato
- **Criterio**: Ordine alfabetico per consistenza

### 2. VERIFICA STATO PROCESSAMENTO E DUPLICATI
- **File di controllo**: `done_pdf.txt` (da creare se non esiste)
- **Formato**: Un path per riga dei PDF già completati + status
- **Azione**: Verificare se il path del PDF corrente è già presente
- **Se presente**: Passare al PDF successivo
- **Se assente**: Procedere con verifica duplicati

#### 2.1 Analisi Duplicati
- **Identificazione**: Confrontare nome file, dimensione, e contenuto con PDF già processati
- **Tipi di duplicati**:
  - **Identici**: Stesso contenuto, stesso formato
  - **Versioni**: Contenuto simile ma versioni diverse (v1.0, v2.0)
  - **Traduzioni**: Stesso contenuto in lingue diverse
  - **Parziali**: Sovrapposizione parziale di contenuti

#### 2.2 Strategia per Duplicati
- **Se identico completo**: 
  - Non processare
  - Aggiungere a `done_pdf.txt` con flag "DUPLICATE_SKIPPED"
  - Annotare riferimento al PDF primario già processato
- **Se versione diversa**:
  - Processare entrambi
  - Annotare relazione nel JSON
  - Marcare quale è la versione principale
- **Se traduzione**:
  - Processare separatamente
  - Annotare lingua e relazione
- **Se parziale**:
  - Processare se contiene informazioni aggiuntive uniche
  - Annotare sovrapposizioni nel JSON

### 3. ESTRAZIONE INFORMAZIONI COMPLETA
**Obiettivo**: Estrarre TUTTE le informazioni presenti nel PDF per uso RAG professionale

#### 3.1 Lettura Manuale Completa
- Leggere ogni pagina del PDF
- Identificare tutte le sezioni e sottosezioni
- Annotare ogni specifica tecnica, procedura, avvertenza

#### 3.2 Identificazione Prodotto
- **Nome prodotto**: Identificazione precisa (es. "Kommander-KA104")
- **Serie**: Famiglia di appartenenza (es. "Kommander")
- **Modello**: Codice specifico (es. "KA104")
- **Tipo**: Categoria (amplificatore, speaker, etc.)

#### 3.3 Estrazione Specifiche Tecniche
- **Audio**: Frequenza, potenza, SPL, impedenza, sensibilità
- **Fisiche**: Dimensioni, peso, materiali, colori
- **Connettività**: Tipi connettori, protocolli, interfacce
- **Alimentazione**: Voltaggio, consumo, efficienza
- **Ambientali**: IP rating, temperatura operativa, umidità
- **Conformità**: Certificazioni, normative, standard

#### 3.4 Estrazione Contenuti Operativi
- **Installazione**: Procedure step-by-step, precauzioni
- **Configurazione**: Settaggi, parametri, opzioni
- **Utilizzo**: Istruzioni operative, best practices
- **Manutenzione**: Pulizia, controlli, sostituzioni
- **Troubleshooting**: Problemi comuni e soluzioni
- **Sicurezza**: Avvertenze, limitazioni, rischi

#### 3.5 Estrazione Informazioni di Supporto
- **Accessori**: Componenti opzionali, kit aggiuntivi
- **Compatibilità**: Prodotti compatibili, limitazioni
- **Garanzia**: Termini, condizioni, procedure
- **Contatti**: Support, assistenza, informazioni aziendali

### 4. CREAZIONE JSON CON TITOLO PARLANTE

#### 4.1 Naming Convention
**Formato**: `extracted_pdf_[incrementale]_[serie]_[modello]_[tipo_documento].json`

**Esempi**:
- `extracted_pdf_001_kommander_ka104_user_guide.json`
- `extracted_pdf_002_domino_kf212_installation_manual.json`
- `extracted_pdf_003_pinnacle_kr402_technical_specs.json`

#### 4.2 Struttura JSON Standardizzata
```json
{
  "id": "pdf_001_kommander_ka104_guide",
  "source_type": "PDF_MANUAL",
  "source_file": "Kommander-KA104_guide_1.pdf",
  "timestamp": "2025-07-13T15:30:00Z",
  "extraction_quality": "manual_verified",
  
  "metadata": {
    "category": "TECHNICAL_DOCUMENTATION",
    "subcategory": "USER_GUIDE",
    "product_line": "Kommander",
    "model": "KA104",
    "document_type": "user_guide",
    "manufacturer": "K-array",
    "page_count": 24,
    "extraction_method": "manual_comprehensive"
  },
  
  "product_identification": {
    "full_name": "Kommander-KA104",
    "series": "Kommander",
    "model": "KA104",
    "type": "4-channel Class D Amplifier",
    "description": "[Descrizione completa dal PDF]"
  },
  
  "technical_specifications": {
    "audio": {
      "channels": "4",
      "power_output": "4 x 2500W @ 4Ω",
      "frequency_response": "20 Hz - 20 kHz (±1 dB)",
      "thd": "[se specificato]",
      "snr": "[se specificato]",
      "source": "[Pagina e sezione specifica del PDF]"
    },
    "physical": {
      "dimensions": "430 x 87 x 430 mm",
      "weight": "8.15 kg",
      "material": "Stainless Steel",
      "color": "Black",
      "ip_rating": "IP20",
      "source": "[Pagina e sezione specifica del PDF]"
    },
    "connectivity": {
      "inputs": "[Dettaglio completo]",
      "outputs": "[Dettaglio completo]",
      "digital": "[Protocolli supportati]",
      "remote": "[Opzioni controllo remoto]",
      "source": "[Pagina e sezione specifica del PDF]"
    },
    "power": {
      "voltage": "[Specifiche alimentazione]",
      "consumption": "[Consumo in diverse condizioni]",
      "efficiency": "[Se specificato]",
      "protection": "[Sistemi protezione]",
      "source": "[Pagina e sezione specifica del PDF]"
    }
  },
  
  "operational_information": {
    "installation": {
      "requirements": "[Requisiti installazione]",
      "procedures": "[Procedure step-by-step]",
      "precautions": "[Precauzioni specifiche]",
      "tools_needed": "[Strumenti necessari]",
      "source": "[Pagina e sezione specifica del PDF]"
    },
    "configuration": {
      "initial_setup": "[Setup iniziale]",
      "dsp_settings": "[Configurazioni DSP]",
      "presets": "[Preset disponibili]",
      "customization": "[Opzioni personalizzazione]",
      "source": "[Pagina e sezione specifica del PDF]"
    },
    "operation": {
      "startup_procedure": "[Procedura accensione]",
      "normal_operation": "[Uso normale]",
      "shutdown_procedure": "[Procedura spegnimento]",
      "monitoring": "[Controllo parametri]",
      "source": "[Pagina e sezione specifica del PDF]"
    },
    "maintenance": {
      "routine_checks": "[Controlli di routine]",
      "cleaning": "[Procedure pulizia]",
      "replacement": "[Sostituzioni componenti]",
      "intervals": "[Intervalli manutenzione]",
      "source": "[Pagina e sezione specifica del PDF]"
    }
  },
  
  "troubleshooting": {
    "common_issues": [
      {
        "problem": "[Descrizione problema]",
        "symptoms": "[Sintomi]",
        "causes": "[Possibili cause]",
        "solutions": "[Soluzioni step-by-step]",
        "source": "[Pagina specifica]"
      }
    ],
    "error_codes": [
      {
        "code": "[Codice errore]",
        "description": "[Descrizione]",
        "action": "[Azione richiesta]",
        "source": "[Pagina specifica]"
      }
    ]
  },
  
  "safety_information": {
    "warnings": "[Avvertenze di sicurezza]",
    "limitations": "[Limitazioni d'uso]",
    "certifications": "[Certificazioni sicurezza]",
    "environmental": "[Condizioni ambientali]",
    "source": "[Pagina e sezione specifica del PDF]"
  },
  
  "support_information": {
    "warranty": {
      "duration": "[Durata garanzia]",
      "coverage": "[Copertura]",
      "exclusions": "[Esclusioni]",
      "procedure": "[Procedura richiesta garanzia]",
      "source": "[Pagina specifica]"
    },
    "accessories": [
      {
        "name": "[Nome accessorio]",
        "code": "[Codice prodotto]",
        "description": "[Descrizione]",
        "compatibility": "[Compatibilità]",
        "source": "[Pagina specifica]"
      }
    ],
    "contacts": {
      "support": "[Contatti supporto tecnico]",
      "sales": "[Contatti commerciali]",
      "website": "[Sito web]",
      "documentation": "[Documentazione aggiuntiva]",
      "source": "[Pagina specifica]"
    }
  },

  "duplicate_management": {
    "is_duplicate": false,
    "duplicate_type": "none|identical|version|translation|partial",
    "related_documents": [
      {
        "file_path": "[Path al documento correlato]",
        "relationship": "primary|secondary|translation|version",
        "notes": "[Note sulla relazione]"
      }
    ],
    "version_info": {
      "version": "[Versione del documento se specificata]",
      "date": "[Data documento se disponibile]",
      "language": "[Lingua del documento]",
      "is_primary_version": true
    },
    "content_overlap": {
      "percentage": "[% di sovrapposizione con altri documenti]",
      "unique_sections": "[Sezioni uniche di questo documento]",
      "overlapping_sections": "[Sezioni che si sovrappongono]"
    },
    "processing_decision": {
      "action": "processed|skipped|merged",
      "reason": "[Motivazione della decisione]",
      "quality_comparison": "[Confronto qualità con documenti simili]"
    }
  },
  
  "embedding_optimized": {
    "searchable_text": "[Testo ottimizzato per ricerca - combinazione di tutte le info chiave]",
    "semantic_chunks": [
      "[Chunk 1: Identificazione prodotto e specifiche principali]",
      "[Chunk 2: Installazione e configurazione]",
      "[Chunk 3: Uso operativo e manutenzione]",
      "[Chunk 4: Troubleshooting e supporto]"
    ],
    "qa_pairs": [
      {
        "question": "[Domanda specifica]",
        "answer": "[Risposta basata su contenuto PDF]",
        "source": "[Pagina e sezione specifica]"
      }
    ],
    "keywords": {
      "primary": "[Parole chiave principali]",
      "technical": "[Termini tecnici]",
      "operational": "[Termini operativi]",
      "troubleshooting": "[Termini risoluzione problemi]"
    }
  },
  
  "source_attributions": [
    {
      "data": "[Informazione specifica]",
      "source": "[Pagina X, sezione Y del PDF]",
      "context": "[Contesto in cui appare l'informazione]"
    }
  ],
  
  "extraction_notes": {
    "extraction_date": "2025-07-13T15:30:00Z",
    "extraction_method": "manual_comprehensive",
    "quality_verified": true,
    "completeness_check": "verified_complete",
    "pages_processed": "[Lista pagine processate]",
    "special_notes": "[Note particolari sull'estrazione]"
  }
}
```

### 5. VERIFICA COMPLETEZZA

#### 5.1 Checklist di Completezza
- [ ] **Identificazione prodotto**: Nome, serie, modello verificati
- [ ] **Specifiche tecniche**: Tutte le specs presenti nel PDF estratte
- [ ] **Informazioni operative**: Installazione, configurazione, uso
- [ ] **Troubleshooting**: Tutti i problemi e soluzioni documentati
- [ ] **Sicurezza**: Tutte le avvertenze e limitazioni
- [ ] **Supporto**: Garanzia, accessori, contatti
- [ ] **Source attribution**: Ogni dato ha riferimento preciso alla pagina
- [ ] **Embedding optimization**: Testo, chunks e Q&A ottimizzati

#### 5.2 Controllo Qualità
- **Confronto diretto**: Ricontrollare il PDF per verificare che non manchi nulla
- **Verifica coerenza**: Controllare che le informazioni siano coerenti
- **Validazione formati**: Verificare che numeri, unità di misura, codici siano corretti
- **Source attribution**: Ogni informazione deve avere il riferimento alla pagina

### 6. FINALIZZAZIONE

#### 6.1 Se Verifica OK
- Salvare il JSON con nome parlante
- Aggiungere il path del PDF al file `done_pdf.txt`
- Passare al PDF successivo

#### 6.2 Se Verifica NOK
- Ripetere il punto 3 (estrazione)
- Identificare cosa manca o è errato
- Correggere il JSON
- Ripetere la verifica

### 7. TRACKING E CONTROLLO

#### 7.1 File di Controllo
**done_pdf.txt** - Formato esteso con gestione duplicati:
```
# Formato: PATH|STATUS|RELATED_DOC|NOTES
data/user_guides/Kommander-KA104_guide_1.pdf|PROCESSED|none|Primary version - complete guide
data/user_guides/Domino-KF212_guide_7.pdf|PROCESSED|none|Complete installation manual
data/user_guides/old/kommander-ka104_user_guide.pdf|DUPLICATE_SKIPPED|data/user_guides/Kommander-KA104_guide_1.pdf|Identical content, older version
data/user_guides/Kommander-KA104_guide_2.pdf|PROCESSED|data/user_guides/Kommander-KA104_guide_1.pdf|Version 2.0 with updates
data/user_guides/Pinnacle-KR402_guide_EN.pdf|PROCESSED|none|English version
data/user_guides/Pinnacle-KR402_guide_IT.pdf|PROCESSED|data/user_guides/Pinnacle-KR402_guide_EN.pdf|Italian translation
```

**Status possibili**:
- `PROCESSED`: Documento completamente elaborato
- `DUPLICATE_SKIPPED`: Duplicato identico saltato  
- `VERSION_PROCESSED`: Versione diversa elaborata
- `TRANSLATION_PROCESSED`: Traduzione elaborata
- `PARTIAL_DUPLICATE`: Duplicato parziale con contenuti unici elaborati

#### 7.2 Log di Estrazione
- Tempo impiegato per PDF
- Difficoltà incontrate
- Note sulla qualità del PDF originale
- Informazioni particolari trovate

## Criteri di Qualità Superiore

### Rispetto ai JSON esistenti, i nuovi devono avere:

1. **Maggiore dettaglio tecnico**: Specifiche più precise e complete
2. **Informazioni operative**: Procedure dettagliate non presenti nei JSON web
3. **Troubleshooting completo**: Problemi e soluzioni specifiche
4. **Source attribution precisa**: Riferimento esatto a pagina e sezione
5. **Semantic chunks ottimizzati**: Chunks specifici per uso RAG
6. **Q&A pairs comprehensive**: Domande e risposte basate su contenuto reale
7. **Zero hallucination**: Solo informazioni effettivamente presenti nel PDF

## Vantaggi di questo Approccio

- **Qualità massima**: Controllo umano su ogni informazione
- **Completezza garantita**: Nessuna informazione persa
- **Tracciabilità perfetta**: Ogni dato ha source preciso
- **RAG ottimizzato**: Struttura pensata per retrieval efficace
- **Scalabilità**: Processo replicabile e controllabile
- **Gestione duplicati intelligente**: Evita ridondanza mantenendo qualità
- **Controllo versioni**: Tracciamento completo di relazioni tra documenti
- **Zero perdita informazioni**: Anche i duplicati parziali vengono valutati

## Note Implementative

- **Tempo stimato**: 30-45 minuti per PDF di media complessità (+10 min per analisi duplicati)
- **Precisione richiesta**: Massima - ogni informazione deve essere verificata
- **Formato rigoroso**: Struttura JSON standardizzata con gestione duplicati
- **Documentazione continua**: Tracking completo del processo e relazioni
- **Gestione duplicati**: 5-10 minuti aggiuntivi per confronto e decisione
- **Controllo qualità**: Verifica finale include controllo anti-ridondanza RAG

## Flowchart Decisionale per Duplicati

```
PDF da processare
      ↓
Confronto con done_pdf.txt
      ↓
Documento già processato? → SÌ → SKIP
      ↓ NO
Analisi duplicati con PDF esistenti
      ↓
Contenuto identico? → SÌ → DUPLICATE_SKIPPED + log
      ↓ NO
Versione diversa? → SÌ → VERSION_PROCESSED + relazione
      ↓ NO  
Traduzione? → SÌ → TRANSLATION_PROCESSED + relazione
      ↓ NO
Duplicato parziale? → SÌ → Valuta contenuti unici → PARTIAL_DUPLICATE se valore aggiunto
      ↓ NO
PROCESSED normale
```

## Criteri di Decisione Duplicati

### Identico (SKIP)
- Hash contenuto uguale
- Nessuna informazione aggiuntiva
- Qualità uguale o inferiore

### Versione (PROCESS)
- Data diversa
- Contenuto aggiornato/corretto
- Nuove sezioni o specifiche

### Traduzione (PROCESS)  
- Lingua diversa
- Possibili dettagli locali
- Valore per utenti multilingue

### Parziale (VALUTA)
- Sovrapposizione >70% ma <100%
- Sezioni uniche significative
- Informazioni complementari