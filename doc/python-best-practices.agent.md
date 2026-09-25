Here are comprehensive AI instructions for Python 3 development, incorporating industry best practices:

---

## 🐍 Python 3 AI Development Best Practices

### Code Structure & Organization

- **Feature Layout**: Use `src/` directory pattern (e.g., `src/feature/`)
- **Module Naming**: snake_case (`file_handler.py`, `user_manager.py`)
- **Class Naming**: PascalCase with first letter uppercase (`UserProfile`, `DataProcessor`)
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

- **Linters**: Use `ruff`
- **Type Hints**: Use `ty`; Always include type annotations for function signatures

```python
def process_user(user_id: int, name: str) -> dict:
    return {"id": user_id, "name": name}
```

### Testing Strategy

- **Unit Tests**: Test individual functions/classes
- **Integration Tests**: Verify component interactions
- **Test Naming**: `test_{functionality}_{condition}_should_{expected_result}`


### Documentation & Comments

- **Docstrings**: Follow Google style for docstrings
- **Comment When**: Explain *why* something is done, not *what*
- **Update Docs**: Keep README and inline docs current with changes

### Security Practices

- **Input Validation**: Always validate user inputs before processing
- **Dependency Audit**: Run `pip-audit` regularly

### Version Control Workflow

- **Atomic Commits**: One logical change per commit
- **Branching**: Feature branches with descriptive names (`feat/add-user-auth`)
- **PR Reviews**: Require at least one reviewer before merging

