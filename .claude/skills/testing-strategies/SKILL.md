# Testing Strategies Skill

> Auto-discovered when testing tasks detected.

## When to Apply

Activates on: "test", "spec", "coverage", "mock", "fixture", "TDD", "integration", "e2e"

## The Testing Pyramid

```
                    /\
                   /  \    E2E Tests
                  /    \   (10% - User flows)
                 /──────\
                /        \
               /          \  Integration Tests
              /            \ (20% - Service boundaries)
             /──────────────\
            /                \
           /                  \  Contract Tests
          /                    \ (20% - FE/BE agreement)
         /────────────────────────\
        /                          \
       /                            \  Unit Tests
      /                              \ (50% - Logic)
     /────────────────────────────────\
```

## Test Types

### Unit Tests (50%)
Test individual functions/methods in isolation.

```python
def test_calculate_discount():
    assert calculate_discount(100, 0.1) == 90
    assert calculate_discount(100, 0) == 100
    assert calculate_discount(0, 0.5) == 0
```

**When to use**: Pure functions, utility methods, business logic

### Contract Tests (20%)
Verify frontend and backend agree on data formats.

```python
def test_frontend_backend_ids_match():
    """Frontend IDs must exist in backend."""
    frontend_ids = ["plan_basic", "plan_pro", "plan_enterprise"]
    backend_ids = list(PRICING_PLANS.keys())

    for fid in frontend_ids:
        assert fid in backend_ids, f"'{fid}' not recognized by backend"
```

**When to use**: API contracts, shared types, ID mappings

### Integration Tests (20%)
Test service boundaries and external integrations.

```python
@pytest.mark.integration
def test_user_creation_with_real_database():
    # Test with actual database, not mocks
    user = create_user("test@example.com", "un42YcgdaeQreBdzKP0PAOyRD4n2")

    assert user.id is not None
    assert User.get(user.id) == user
```

**When to use**: Database operations, external APIs, auth flows

### E2E Tests (10%)
Test complete user journeys.

```python
@pytest.mark.e2e
def test_complete_purchase_flow():
    # Login
    login(TEST_USER)

    # Add to cart
    add_to_cart(PRODUCT_ID)

    # Checkout
    result = checkout(PAYMENT_INFO)

    assert result.status == "success"
    assert get_user_credits() == EXPECTED_CREDITS
```

**When to use**: Critical user paths, smoke tests

### Smoke Tests (Post-Deploy)
Verify deployment succeeded.

```bash
#!/bin/bash
API_URL="${1:-https://api.example.com}"

# Health check
curl -sf "$API_URL/health" || exit 1

# Auth works (should be 401, not 500)
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/api/protected")
[ "$STATUS" -eq 401 ] || exit 1

echo "✓ Smoke tests passed"
```

## Test Fixtures

### Realistic IDs
```python
# Don't use fake UUIDs for auth providers
REALISTIC_USER_IDS = [
    "un42YcgdaeQreBdzKP0PAOyRD4n2",  # Firebase
    "auth0|abc123def456",             # Auth0
    "google-oauth2|123456789",        # Google
    str(uuid.uuid4()),                # Actual UUID
]

@pytest.mark.parametrize("user_id", REALISTIC_USER_IDS)
def test_user_operations(user_id):
    user = create_user(user_id)
    assert user.success
```

### Test Data Factories
```python
from faker import Faker
fake = Faker()

def make_user(**overrides):
    return {
        "email": fake.email(),
        "name": fake.name(),
        "created_at": fake.date_time(),
        **overrides
    }
```

## Mocking Guidelines

### Do Mock
- External APIs (Stripe, SendGrid)
- Time/dates for determinism
- Random values

### Don't Mock
- Your own code (test the real thing)
- Database in integration tests
- Auth providers in integration tests

## Coverage Targets

| Type | Target | Rationale |
|------|--------|-----------|
| Unit | 80%+ | Core logic covered |
| Integration | Key paths | Service boundaries |
| Contract | 100% | All shared types |
| E2E | Critical paths | User journeys |

## Test Organization

```
tests/
├── unit/                 # Fast, isolated
│   ├── test_utils.py
│   └── test_services.py
├── integration/          # Slower, real deps
│   ├── test_database.py
│   └── test_auth.py
├── contracts/            # FE/BE agreement
│   └── test_api_contracts.py
├── e2e/                  # Full flows
│   └── test_purchase.py
├── fixtures/             # Shared test data
│   ├── users.py
│   └── products.py
└── conftest.py           # Pytest config
```

## Running Tests

```bash
# Unit tests (fast)
pytest tests/unit -v

# Integration (needs DB)
pytest tests/integration -v --tb=short

# Contracts (CI blocker)
pytest tests/contracts -v

# E2E (slow)
pytest tests/e2e -v --slow

# All with coverage
pytest --cov=src --cov-report=html
```

## CI Configuration

```yaml
test:
  stages:
    - unit        # Fast, run first
    - contracts   # Block if FE/BE mismatch
    - integration # Real database
    - e2e         # Full flows (optional on PR)
```
