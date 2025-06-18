"""Wrapper per l'esecuzione della knowledge pipeline modulare."""
from knowledge_pipeline import cli, KnowledgePipeline, PipelineConfig

__all__ = ["KnowledgePipeline", "PipelineConfig", "cli"]

if __name__ == "__main__":
    cli()
