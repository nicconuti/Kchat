from categorizer.chunk_builders import build_price_chunks, build_chunks

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

def test_build_price_chunks():
    rows = build_price_chunks(PRICE_TABLE)
    assert rows == [
        {"serial": "1", "subcategory": "Hardware", "description": "Base kit", "price": "50"},
        {"serial": "2", "subcategory": "Software", "description": "Pro kit", "price": "100"},
    ]


def test_build_price_chunks_newline_format():
    rows = build_price_chunks(PRICE_LINES)
    assert rows == [
        {"serial": "1", "subcategory": "Hardware", "description": "Base kit", "price": "50"},
        {"serial": "2", "subcategory": "Software", "description": "Pro kit", "price": "100"},
    ]


def test_build_chunks_dispatch():
    chunks = build_chunks(PRICE_TABLE, "product_price")
    assert len(chunks) == 2
    assert chunks[0]["serial"] == "1"


def test_build_chunks_dispatch_newline():
    chunks = build_chunks(PRICE_LINES, "product_price")
    assert len(chunks) == 2
    assert chunks[1]["price"] == "100"
