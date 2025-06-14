from pathlib import Path
from categorizer import (
    extract_subcategories,
    classify,
    score,
    extract_text,
    Categorizer,
)
from categorizer.validator import confirm
from openpyxl import Workbook  # type: ignore


def test_score():
    assert score("bug bug", ["bug"]) == 1
    assert score("no match", ["bug"]) == 0


def test_extract_subcategories():
    text = "Lo speaker non funziona. Il bug causa problemi allo speaker."
    subs = extract_subcategories(text, max_terms=3)
    assert "speaker" in subs
    assert "bug" in subs


def test_classify():
    text = "manuale per speaker rotto"
    cat, subs, conf, amb = classify(text, "doc.txt")
    assert cat == "product_guide" or cat == "tech_assistance"
    assert isinstance(subs, list)
    assert conf > 0
    assert isinstance(amb, bool)


def test_confirmation_auto(monkeypatch):
    inputs = iter(["n", "product_price", "speaker,bug"])
    monkeypatch.setattr("builtins.input", lambda *_: next(inputs))
    category, subcats, validated, source, conf = confirm(
        "tech_assistance",
        ["speaker"],
        "bug nel sistema",
        "bug.txt",
        mode="interactive",
        confidence=0.4,
    )
    assert validated
    assert source == "human_override"


def test_categorizer_run(tmp_path: Path):
    sample = tmp_path / "help.txt"
    sample.write_text("Lo speaker non funziona, ho un problema. C'e' un bug.")
    cat = Categorizer(mode="auto")
    results = cat.run(tmp_path)
    assert results[0]["category"] == "tech_assistance"
    assert "speaker" in results[0]["subcategories"]
    assert "entities" in results[0]["metadata"]


def test_extract_xlsx(tmp_path: Path):
    sample = tmp_path / "data.xlsx"
    wb = Workbook()
    ws = wb.active
    ws["A1"] = "hello"
    ws["A2"] = "world"
    wb.save(sample)
    text = extract_text(sample)
    assert "hello" in text
    assert "world" in text
