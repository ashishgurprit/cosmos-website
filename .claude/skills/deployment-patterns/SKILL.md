# Deployment Patterns Skill

> Auto-discovered when deployment tasks detected.

## When to Apply

Activates on: "deploy", "production", "staging", "release", CI/CD configuration

## Core Principle: Fail Fast, Fail Loud

Every deployment issue from LESSONS.md could have been caught with:
1. Startup validation
2. Contract tests
3. Integration tests with realistic data
4. Post-deployment smoke tests

## Pre-Deploy Checklist (from lessons)

### Environment
- [ ] All required env vars set
- [ ] Secrets in correct format
- [ ] API keys match environment

### Identity & Auth
- [ ] Tested with REAL auth IDs
- [ ] UUID conversion handles all formats
- [ ] Headers pass through proxy

### Database
- [ ] Migrations separate from startup
- [ ] ID types match auth provider
- [ ] Connection pool sized

### API
- [ ] Contract tests pass
- [ ] Errors are displayed
- [ ] CORS configured

### Payments (if applicable)
- [ ] Webhooks transactional
- [ ] Test vs live keys correct

## Smoke Test After Deploy

```bash
#!/bin/bash
API_URL="${1:-https://api.example.com}"

# Health
curl -sf "$API_URL/health" || exit 1

# Auth (should be 401, not 500)
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/api/protected")
[ "$STATUS" -eq 401 ] || exit 1

echo "✓ Smoke tests passed"
```

## Common Failures

| Pattern | Symptom | Fix |
|---------|---------|-----|
| Silent config fail | Feature breaks at runtime | Startup validation |
| ID format mismatch | "Invalid UUID" in prod | Test with real IDs |
| Contract drift | UI does nothing | Contract tests |
| Header loss | 401 only in prod | Proxy config |
| Partial webhook | Payment OK, no credits | Transactional handler |
