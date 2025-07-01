"""Wrapper per l'esecuzione della knowledge pipeline modulare."""
from knowledge_pipeline import cli, KnowledgePipeline, PipelineConfig
from karray_rag import karray_rag_pipeline
from haystack.dataclasses import Document

__all__ = ["KnowledgePipeline", "PipelineConfig", "cli"]

if __name__ == "__main__":
    cli()
    karray_rag_pipeline.run_pipeline_with_karray()
