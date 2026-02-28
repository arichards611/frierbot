---
applyTo: "**/*.py"
---

# Coding Style Conventions

## Brevity & Expression Rules

### Prefer list comprehensions over manual loops
```python
# Bad
def get_even_squares(nums):
    result = []
    for n in nums:
        if n % 2 == 0:
            squared = n * n
            result.append(squared)
    return result

# Good
def get_even_squares(nums):
    return [n * n for n in nums if n % 2 == 0]
```

### Collapse simple if/else into ternary expressions
```python
# Bad
if user is not None:
    name = user.name
else:
    name = "Guest"

# Good
name = user.name if user is not None else "Guest"
```

### Prefer single-expression returns
Return the expression directly instead of assigning to a temporary variable and returning it.

### Avoid unnecessary temporary variables
Only introduce a variable when it improves readability or is reused.

### Favor functional patterns over imperative multi-line logic
Prefer `map`, `filter`, comprehensions, and generator expressions over explicit loops when the intent is clear.

## Reusability & Abstraction Rules

### Prefer generic base abstractions over duplicated specialized classes
```python
# Bad — duplicated logic across domain classes
class CarDB:
    def insert(self, car): ...
    def delete(self, car_id): ...
    def get(self, car_id): ...

class UserDB:
    def insert(self, user): ...
    def delete(self, user_id): ...
    def get(self, user_id): ...

# Good — generic base, specialize only what differs
class BaseDB:
    def __init__(self, table_name, connection):
        self.table_name = table_name
        self.connection = connection

    def insert(self, data): ...
    def delete(self, record_id): ...
    def get(self, record_id): ...

class CarDB(BaseDB):
    def __init__(self, connection):
        super().__init__("cars", connection)
```

Or, when no override is needed, use composition directly:
```python
cars = Table("cars", conn)
users = Table("users", conn)
```

### Parameterize differences instead of duplicating logic
Use constructor args, config dicts, or `**kwargs` to express variation.

### Prefer batch APIs over single-item methods
```python
# Bad — read/modify/patch per key
def set(self, key: str, value: str) -> None:
    configmap = read_configmap(...)
    configmap.data[key] = value
    patch_configmap(...)

# Good — one read/modify/patch for N keys
def set(self, **kwargs: str) -> None:
    configmap = read_configmap(...)
    if configmap.data is None:
        configmap.data = {}
    configmap.data.update(kwargs)
    patch_configmap(...)
```

### Composition over inheritance — unless behavior must be overridden
Use inheritance when subclasses need to change behavior. Otherwise prefer composition or parameterization.

## When NOT to Abstract

Abstract when duplication appears twice, not before it appears once. Premature abstraction adds complexity without proven value.
