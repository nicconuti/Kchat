import os
from utils.logger import get_logger


def test_logger_fields(tmp_path):
    os.chdir(tmp_path)
    logger = get_logger("sample")
    logger.info(
        "hello",
        extra={
            "confidence_score": 0.5,
            "source_reliability": 0.8,
            "clarification_attempted": True,
            "error_flag": False,
        },
    )
    log_file = tmp_path / "logs" / "sample.log"
    text = log_file.read_text()
    assert "confidence=0.5" in text
    assert "reliability=0.8" in text
    assert "clarification=True" in text
    assert "error=False" in text
