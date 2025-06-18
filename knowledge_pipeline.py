"""Wrapper per l'esecuzione della knowledge pipeline modulare."""
from pipeline import cli, KnowledgePipeline, PipelineConfig

__all__ = ["KnowledgePipeline", "PipelineConfig", "cli"]

if __name__ == "__main__":
    cli()
