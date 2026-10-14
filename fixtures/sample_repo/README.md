# Sample Demo Repository for BlackBox

This repository is provided as a ready-to-import fixture for testing BlackBox features:

1. **AST & Symbol Extraction**: Contains `calculate_discount`, `compute_tax`, and the `OrderProcessor` class.
2. **Architecture Graph**: Contains an inter-file dependency (`service.py` imports `calculator.py`).
3. **AI Autonomous Investigation**: Ask *"How does OrderProcessor calculate discounts and taxes?"* to see grounded code reasoning.
4. **Sandboxed Testing**: Execute `pytest tests/test_calculator.py` inside the BlackBox sandbox.
