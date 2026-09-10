from app.qc import find_novel_numeric_unit_claims


def test_allows_source_numeric_value():
    source = "Amiodarone may be given as 300 mg intravenously."
    script = "A common dose stated here is 300 mg intravenously."
    assert find_novel_numeric_unit_claims(source, script) == []


def test_blocks_new_numeric_value():
    source = "Amiodarone may be given as 300 mg intravenously."
    script = "Give 150 mg intravenously."
    assert find_novel_numeric_unit_claims(source, script) == ["150 mg"]
