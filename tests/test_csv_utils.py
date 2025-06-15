from utils.csv_utils import load_csv, summarize_csv


def test_load_csv_with_header(tmp_path):
    csv = tmp_path / "data.csv"
    csv.write_text("a,b\n1,2\n3,4\n")
    records = load_csv(csv)
    assert records == [{"a": 1, "b": 2}, {"a": 3, "b": 4}]


def test_load_csv_without_header(tmp_path):
    csv = tmp_path / "data.csv"
    csv.write_text("1,2\n3,4\n")
    records = load_csv(csv)
    assert records == [{"col_0": 1, "col_1": 2}, {"col_0": 3, "col_1": 4}]


def test_summarize_csv(monkeypatch, tmp_path):
    csv = tmp_path / "data.csv"
    csv.write_text("a,b\n1,2\n")
    monkeypatch.setattr("utils.csv_utils.call_mistral", lambda prompt: "two columns a and b")
    summary = summarize_csv(csv)
    assert "two columns" in summary
