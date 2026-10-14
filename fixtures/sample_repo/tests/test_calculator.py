from app.calculator import calculate_discount, compute_tax


def test_calculate_discount():
    assert calculate_discount(100.0, 10.0) == 90.0
    assert calculate_discount(200.0, 50.0) == 100.0


def test_compute_tax():
    assert compute_tax(100.0, 0.10) == 10.0
