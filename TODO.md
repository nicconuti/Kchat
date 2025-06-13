# TODO

## 1. Transparency Logging
- **Description**: Include `confidence_score`, `source_reliability`, `clarification_attempted` and `error_flag` in each log entry. Update logger and agents accordingly.
- **Destination**: `/utils`, `/agents`
- **Dependencies**: none

## 2. Dynamic Orchestrator
- **Description**: Make `OrchestratorAgent` choose the agent sequence via LLM prompting, storing the reasoning trace in context.
- **Destination**: `/agents`
- **Dependencies**: task 1

## 3. Log-Based Self-Evaluation
- **Description**: Extend `SupervisorAgent` to analyze logs for misclassifications and weak answers, generating improvement suggestions.
- **Destination**: `/agents`
- **Dependencies**: task 1

## 4. Qdrant Retrieval
- **Description**: Connect `DocumentRetrieverAgent` to a Qdrant instance and enforce user permissions during retrieval.
- **Destination**: `/agents`
- **Dependencies**: none

## 5. Embedding Ingestion Pipeline
- **Description**: Enhance `EmbeddingIngestorAgent` to parse documents, chunk text, generate embeddings and upload them to Qdrant.
- **Destination**: `/agents`
- **Dependencies**: task 4
