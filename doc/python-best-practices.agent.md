Here are comprehensive AI instructions for Python 3 development, incorporating industry best practices:

---

## 🐍 Python 3 AI Development Best Practices

### Code Structure & Organization

- **Feature Layout**: Use `src/` directory pattern (e.g., `src/feature/`)
- **Module Naming**: Snake case (`file_handler.py`, `user_manager.py`)
- **Class Naming**: CamelCase with first letter uppercase (`UserProfile`, `DataProcessor`)
- **One Class Per File**: Always keep classes in dedicated modules
- **Import Organization**:
- do not use conditional imports; always import at top of file

```python
# Standard library
import os
from typing import List

# Third-party
from PySide6.QtWidgets import QMainWindow

# Local imports
from .utils.helpers import format_date
```

### Code Quality & Linting

- **Linters**: Use `ruff` (fast, modern) or `flake8`
- **Type Hints**: Always include type annotations for function signatures

```python
def process_user(user_id: int, name: str) -> dict:
    return {"id": user_id, "name": name}
```

- **Static Analysis**: Run `mypy` in CI/CD pipelines
- **Format Code**: Use `black` with consistent line length (88 chars)

### Testing Strategy

- **Unit Tests**: Test individual functions/classes
- **Integration Tests**: Verify component interactions
- **Test Naming**: `test_{functionality}_{condition}_should_{expected_result}`

```python
def test_calculate_discount_when_user_is_premium_should_apply_20_percent():
# test implementation
```

### Documentation & Comments

- **Docstrings**: Follow Google style for docstrings
- **Comment When**: Explain *why* something is done, not *what*
- **Update Docs**: Keep README and inline docs current with changes

### Security Practices

- **Input Validation**: Always validate user inputs before processing
- **Dependency Audit**: Run `pip-audit` regularly
- **Environment Variables**: Use `.env` files (add to `.gitignore`)

```python
from dotenv import load_dotenv

load_dotenv()
```

### Performance Optimization

- **Profile First**: Use `cProfile` before optimizing
- **Memory Management**: Context managers for resources

```python
with open("file.txt") as f:
    data = f.read()
```

- **Lazy Evaluation**: Use generators for large datasets

### Version Control Workflow

- **Atomic Commits**: One logical change per commit
- **Branching**: Feature branches with descriptive names (`feat/add-user-auth`)
- **PR Reviews**: Require at least one reviewer before merging

