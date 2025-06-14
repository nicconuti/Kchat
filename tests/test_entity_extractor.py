from categorizer.entity_extractor import extract_entities


def test_extract_entities():
    text = "L'errore compare in Microsoft Word quando avvio KChat."
    ents = extract_entities(text)
    assert "Microsoft Word" in ents
    assert "KChat" in ents
