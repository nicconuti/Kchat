#  AGENTS.md — Agentic Orchestration Guide for Customer Care Chatbot

## 📌 Project Context

This repository implements a **local-first, multilingual, agentic chatbot** for handling customer support tasks such as:

* Answering frequently asked questions (FAQs)
* Retrieving documents from a 1.5GB knowledge base (PDF, DOCX, XLSX)
* Generating and sending estimation of fees and costs (PDF via email)
* Logging support tickets and booking meets
* Asking clarifying questions in case of ambiguity

The chatbot is designed to work **without any external APIs**, running on a **MacBook M2 Pro 16GB RAM**, using models served via **Ollama**.

---

## 🧠 Agentic Architecture Overview

Each functional unit is modularized as a **single-responsibility agent**. These agents can be invoked by an orchestrator and will evolve into fully autonomous sub-systems with memory, task state, and interaction capabilities.

### Core Agents

#### IntentAgent

* **Goal**: Classify the user's intent to drive agentic routing
* **Skills**: Example-based and rule-based classification
* **Memory**: Learns from historical logs
* **Output**:

  ```json
  {
    "intent": "open_ticket",
    "confidence": 0.92
  }
  ```

* **Supported Intents**:

| **Intent**                    | **Description**                                                                                        | **User Example**                                               |
| ----------------------------- | ------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------- |
| `technical_support_request`   | The user has a technical issue with an existing product, software, or service                          | *"My device won’t turn on anymore, can you help me?"*          |
| `product_information_request` | The user is asking for detailed information about a product or service (features, compatibility, etc.) | *"Does this model support Bluetooth?"*                         |
| `estimation_costs`            | The user wants a quote or pricing information                                                          | *"Can you give me a quote for model XXX?"*                     |
| `schedule`                    | Request to schedule an appointment, installation, or demo                                              | *"I’d like to schedule a meeting with a technician for setup"* |
| `document_request`            | The user asks for a document, certificate, manual, technical sheet, etc.                               | *"Could I get the manual in PDF?"*                             |
| `open_ticket`                 | The user explicitly asks to open a support ticket                                                      | *"Please open a ticket, I can’t solve this issue"*             |
| `complaint`                   | The user expresses a formal complaint or dissatisfaction                                               | *"The product arrived damaged, I’m very disappointed"*         |
| `generic_smalltalk`           | The input is not classifiable (greetings, casual phrases, test messages, etc.)                         | *"Hi, is there any event scheduled in the k-hall?"*            |

#### LanguageAgent

* **Goal**: Detect user input language and syntax quality
* **Extensions**:

  * Formality detection
  * Mixed-language identification
  * Speech-to-text integration

#### TranslationAgent

* **Goal**: Translate user input/output when necessary
* **Extensions**:

  * Auto-correction if input language is wrongly inferred
  * Stylistic adaptation (formal, technical, friendly)

#### DocumentRetrieverAgent

* **Goal**: Perform semantic retrieval over indexed documentation (1.5GB of PDFs, DOCXs, etc.). In the future, it will also need to verify whether the user has access to the requested documents or information.
* **Retrieval Model**: Qdrant + embeddings (`text-embedding-3`, `BGE-M3`, `LaBSE`)
* **Output**: Top-k chunks with metadata and document source
* **Future Enhancements**:

  * Checks user permission and compare with documents.
  * stop the process if user has no view right.

#### ResponseAgent

* **Goal**: Generate the final response shown to the user
* **Modes**:

  * **SimpleResponder**: generates a response directly from the LLM without consulting any document or triggering any backend action. Ideal for general, casual, or smalltalk interactions.

    * *Example*: "What are your opening hours?"
  * **DocGroundedResponder**: generates a response using retrieved document chunks provided by `DocumentRetrieverAgent`. It is designed for factual grounding, citations, and document-based answers.

    * *Example*: "Can you explain section 4 of the installation manual?"
  * **ActionResponder**: composes a response based on the result of a backend operation (e.g., ticket creation, quote generation), often working in tandem with `ActionAgent` or `QuotationAgent`.

    * *Example*: "Your support ticket has been created with ID #34872."
* **Prompting**:

  * Style-conditioned (formal, technical, friendly)
  * Context-aware (conversation history, session)
  * Optionally constrained to use only verified source data (DocGrounded mode)
* **Fallback**: If no response is confidently generated, triggers `ClarificationAgent` with a prompt to rephrase or specify user intent.

#### ClarificationAgent

* **Goal**: Ask for clarification when input is ambiguous or confidence is low
* **Behavior**:

  * Triggered if intent confidence < threshold or if verification fails
  * Generates one or more rephrased questions to resolve ambiguity
  * Adapts tone (friendly, professional, technical) depending on user profile or detected language register
  * Personalizes based on conversation history and known context
* **Future Enhancements**:

  * Dynamic probing strategy: generates increasingly specific follow-ups
  * Learns optimal clarification phrasing via log feedback

#### 🧪 VerificationAgent

* **Goal**: Validate the utility and factual consistency of a response
* **Extensions**:

  * Voting across multiple LLM generations
  * Self-feedback loop from logs or user feedback
  * Output classification (✅ valid / ⚠️ uncertain / ❌ incorrect)

#### 🧾 QuotationAgent

* **Goal**: Generate a PDF quote and send it to the user
* **Triggers**: `quote_request` intent
* **Extensions**:

  * CRM/ERP integration
  * Discount logic and validity rules
  * Quote versioning and status tracking

#### 🛠️ ActionAgent

* **Goal**: Perform concrete backend operations (e.g., open a ticket, schedule intervention)
* **Backend**: Interface with internal APIs or subprocess task runner
* **Extensions**: Dynamic multi-step workflows, dry-run validation mode

#### 🧠 OrchestratorAgent

* **Goal**: Decide which agents to invoke and in what order based on user input
* **Modes**:

  * Phase 1: Rule-based
  * Phase 2: Dynamic prompting (Mistral 7B)
  * Phase 3: Graph-based (LangGraph, AutoGen, Toolformer)
* **State**: Tracks short-term session, conversation metadata, agent outputs
* **Memory**:

  * Transient: message history, language, intent
  * Persistent: user feedback, session summaries, clarification records
* **Logging**:

  * `orchestration_trace`: records reasoning chain and agent sequence used

---

## 📚 RAG Pipeline (Retrieval-Augmented Generation)

### Documents Ingestion

Handled by a background `EmbeddingIngestorAgent` that:

* Parses documents from Google Drive or local FS
* Uses `pdfplumber`, `unstructured`, `mammoth`, `pandas` for parsing
* Applies semantic chunking (500–1000 tokens)
* Generates embeddings with `BGE-M3`, `LaBSE`, or `text-embedding-3`
* Uploads data to **Qdrant** with metadata:

```json
{
  "chunk": "...",
  "doc_type": "manual",
  "lang": "en",
  "source": "support_doc_v3.pdf",
  "created_at": "2024-04-01"
}
```

### Query Flow

> ⚠️ **Note:** To ensure maximum accuracy across languages, the detection of user intent should occur **after language detection and optional translation to a pivot language (typically English)**. This avoids errors due to partial understanding in non-native languages.

```txt
User input
  ↓
OrchestratorAgent
  ├──> LanguageAgent
  ├──> TranslationAgent (if input language ≠ pivot)
  ├──> IntentAgent → intent = 'faq' or 'recupera_documento'
  ├──> DocumentRetrieverAgent → top-k chunks
  ├──> ResponseAgent (DocGrounded mode)
  ├──> VerificationAgent
  ├──> ClarificationAgent (if triggered by low confidence or ambiguity)
  └──> TranslationAgent (if language mismatch)
↓
Final Output (grounded, localized response)
```

---

## 🔄 Shared Memory Schema

All agents receive and emit data through a shared `AgentContext`:

```json
{
  "user_id": "abc123",
  "session_id": "sess-456",
  "input": "User message here",
  "language": "it",
  "intent": "quote_request",
  "confidence": 0.84,
  "documents": [...],
  "response": "Final LLM response",
  "clarification_attempted": true
}
```

---

## 📋 Logging Responsibilities

| Agent              | Log Channels              |
| ------------------ | ------------------------- |
| IntentAgent        | `intent_log`              |
| LanguageAgent      | `lang_log`                |
| DocumentRetriever  | `retrieval_log`           |
| ResponseAgent      | `chat_log`, `source_used` |
| ClarificationAgent | `clarification_log`       |
| VerificationAgent  | `validation_log`          |
| OrchestratorAgent  | `orchestration_trace`     |

---

## ✅ How to Contribute

### 🔍 Explore only

* `/agents/` — All agent modules go here.
* `/retriever/` — Document ingestion, indexing, retrieval.
* `/frontend/` — React-based frontend.
* `/logs/` — Language, action, validation logs.
* `/prompts/` — All prompt templates.

### ❌ Do NOT

* Use cloud APIs or paid services
* Change logging structure without approval
* Modify internal DSLs or prompt formats silently

### 🧪 Testing

* Unit tests live in `/tests/`
* Run: `pytest`
* Lint: `ruff .`, Type check: `mypy .`

---

## 🌟 Continuous Improvement & Self-Criticism

To support long-term robustness and evolution:

* **Self-Evaluation**: Each agent should regularly reprocess prior logs to assess:

  * Misclassifications (e.g., IntentAgent mismatch)
  * Incorrect responses (e.g., ResponseAgent hallucinations)
  * Weak grounding (e.g., RetrieverAgent with poor chunks)
  * Ineffective clarifications (e.g., ClarificationAgent not resolving ambiguity)

* **Meta Feedback Loop**: Implement a supervisor routine (weekly/cron) that:

  * Collects thumbs up/down or validation mismatches
  * Logs and ranks agent failures
  * Generates improvement prompts for agent retraining or refactoring

* **Failure-Driven Learning**: Encourage agents to admit uncertainty ("I'm not confident in this answer") and trigger ClarificationAgent when needed.

* **Transparency Logging**: Add fields in logs for `confidence_score`, `source_reliability`, `clarification_attempted`, `error_flag`

---

## 🧠 Bonus Agentic Features (Future)

* Self-healing: Agents detect their own failure and recover autonomously
* Proactive interaction: Agent proposes next steps or helpful actions
* Explainability: Agents justify choices and explain their reasoning
* Agent devtools: Interface to inspect live agent decisions, memory, logs
* Auto-evaluation: Periodic analysis of logs for automated fine-tuning and improvement suggestions

---

**This file is intended as a blueprint and operational guide for both developers and autonomous agents working within this repository.**
