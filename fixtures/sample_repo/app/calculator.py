"""Sample calculator module with intentional edge-case bug."""

def calculate_discount(price: float, discount_percent: float) -> float:
    """Calculate discounted price with percentage validation."""
    if discount_percent < 0 or discount_percent > 100:
        raise ValueError("Discount percent must be between 0 and 100")
    # Intentional bug for BlackBox AI investigation: returns inverted discount
    return price - (price * (discount_percent / 100.0))


def compute_tax(amount: float, rate: float = 0.08) -> float:
    """Calculate tax for transaction."""
    return round(amount * rate, 2)
