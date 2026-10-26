from src.modules.decide import Candidate, decide


def num(v):
    return Candidate("number", v, "SELECT 1")


def failed():
    return Candidate("pending", error="boom")


def test_unanimous_answer():
    d = decide([num(5), num(5), num(5)], tau=0.67)
    assert d.answer.type == "number" and d.answer.value == 5
    assert d.agreement == 1.0


def test_majority_above_tau():
    d = decide([num(5), num(5), num(6)], tau=0.6)
    assert d.answer.value == 5
    assert round(d.agreement, 2) == 0.67


def test_low_agreement_abstains_but_keeps_top():
    d = decide([num(5), num(6), num(7)], tau=0.5)
    assert d.answer.type == "abstain"
    assert d.top.value == 5  # first seen wins the tie
    assert round(d.agreement, 2) == 0.33


def test_failed_candidates_count_against_agreement():
    d = decide([num(5), failed(), failed()], tau=0.5)
    assert d.answer.type == "abstain"
    assert round(d.agreement, 2) == 0.33


def test_all_failed_abstains():
    d = decide([failed(), failed()], tau=0.0)
    assert d.answer.type == "abstain" and d.top is None and d.agreement == 0.0


def test_unanswerable_vote():
    d = decide([Candidate("unanswerable"), Candidate("unanswerable"), num(1)], tau=0.6)
    assert d.answer.type == "unanswerable" and d.answer.value is None


def test_strings_vote_case_and_nfc_insensitive():
    a = Candidate("string", "Cà phê")
    b = Candidate("string", "cà phê ")
    d = decide([a, b], tau=1.0)
    assert d.answer.value == "Cà phê"


def test_int_and_float_vote_together():
    d = decide([num(3), num(3.0)], tau=1.0)
    assert d.answer.type == "number"


def test_tie_break_is_deterministic():
    one = decide([num(1), num(2)], tau=0.0)
    two = decide([num(1), num(2)], tau=0.0)
    assert one.answer == two.answer and one.answer.value == 1
