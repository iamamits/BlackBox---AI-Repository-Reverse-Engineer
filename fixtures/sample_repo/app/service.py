"""Order processing service demonstrating inter-file dependencies."""
from app.calculator import calculate_discount, compute_tax


class OrderProcessor:
    """Processes customer carts and computes totals."""

    def __init__(self, tax_rate: float = 0.08):
        self.tax_rate = tax_rate

    def checkout(self, items: list[dict], discount: float = 0.0) -> dict:
        subtotal = sum(item["price"] * item.get("quantity", 1) for item in items)
        discounted = calculate_discount(subtotal, discount)
        tax = compute_tax(discounted, self.tax_rate)
        return {
            "subtotal": subtotal,
            "discount": discount,
            "tax": tax,
            "total": round(discounted + tax, 2),
        }
