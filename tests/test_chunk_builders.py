import pandas as pd
from categorizer.chunk_builders import parse_price_table, build_chunks
from categorizer.price_chunk_builder import parse_price_table_from_excel

PRICE_TABLE = """
Serial | Subcategory | Description | Price
1 | Hardware | Base kit | 50
2 | Software | Pro kit | 100
"""

PRICE_LINES = """
Serial
Subcategory
Description
Price
1
Hardware
Base kit
50
2
Software
Pro kit
100
"""

def test_parse_price_table():
    rows = parse_price_table(PRICE_TABLE)
    assert rows == [
        {"serial": "1", "subcategory": "Hardware", "description": "Base kit", "price": "50"},
        {"serial": "2", "subcategory": "Software", "description": "Pro kit", "price": "100"},
    ]


def test_parse_price_table_newline_format():
    rows = parse_price_table(PRICE_LINES)
    assert rows == [
        {"serial": "1", "subcategory": "Hardware", "description": "Base kit", "price": "50"},
        {"serial": "2", "subcategory": "Software", "description": "Pro kit", "price": "100"},
    ]


def test_parse_price_table_with_parent():
    rows = parse_price_table(PRICE_TABLE, parent_category="Main")
    assert rows == [
        {"serial": "1", "subcategory": "Main, Hardware", "description": "Base kit", "price": "50"},
        {"serial": "2", "subcategory": "Main, Software", "description": "Pro kit", "price": "100"},
    ]


def test_build_chunks_dispatch():
    chunks = build_chunks(PRICE_TABLE, "product_price")
    assert len(chunks) == 2
    assert chunks[0]["serial"] == "1"


def test_build_chunks_dispatch_newline():
    chunks = build_chunks(PRICE_LINES, "product_price")
    assert len(chunks) == 2
    assert chunks[1]["price"] == "100"


def test_parse_price_table_from_csv(monkeypatch, tmp_path):
    csv = tmp_path / "prices.csv"
    csv.write_text("code,name,cost\n1,Base kit,50\n2,Pro kit,100\n")
    df = pd.read_csv(csv)
    monkeypatch.setattr(
        "categorizer.price_chunk_builder.infer_column_mapping_with_llm",
        lambda _df: {"serial": "code", "description": "name", "price": "cost"},
    )
    rows = parse_price_table_from_excel(df)
    assert rows == [
        {"serial": "1", "subcategory": "", "description": "Base kit", "price": "50"},
        {"serial": "2", "subcategory": "", "description": "Pro kit", "price": "100"},
    ]


def test_parse_price_table_from_excel(monkeypatch, tmp_path):
    data = pd.DataFrame({"id": ["1", "2"], "desc": ["A", "B"], "price": ["10", "20"]})
    xls = tmp_path / "data.xlsx"
    data.to_excel(xls, index=False)
    df = pd.read_excel(xls)
    monkeypatch.setattr(
        "categorizer.price_chunk_builder.infer_column_mapping_with_llm",
        lambda _df: {"serial": "id", "description": "desc", "price": "price"},
    )
    rows = parse_price_table_from_excel(df)
    assert rows == [
        {"serial": "1", "subcategory": "", "description": "A", "price": "10"},
        {"serial": "2", "subcategory": "", "description": "B", "price": "20"},
    ]
