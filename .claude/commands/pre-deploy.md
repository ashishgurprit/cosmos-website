---
description: Pre-deployment checklist with lessons applied
allowed-tools: ["Read", "Bash", "Task", "Glob"]
---

# Pre-Deployment Checks

Comprehensive checks before deploying, incorporating lessons learned and documentation verification.

## Instructions

### Phase 1: Load Lessons

Read lessons from:
1. `.claude/LESSONS.md` (master lessons)
2. `.claude/LESSONS-PROJECT.md` (project-specific)

Extract all prevention checklist items.

### Phase 2: Environment Validation

Check configuration:

```bash
# Required environment variables
echo "=== Environment Check ==="

# List based on project type
REQUIRED_VARS="DATABASE_URL"

# Add based on detected features
if grep -q "stripe" package.json pyproject.toml 2>/dev/null; then
    REQUIRED_VARS="$REQUIRED_VARS STRIPE_SECRET_KEY STRIPE_WEBHOOK_SECRET"
fi

if grep -q "firebase" package.json pyproject.toml 2>/dev/null; then
    REQUIRED_VARS="$REQUIRED_VARS FIREBASE_CREDENTIALS"
fi

for var in $REQUIRED_VARS; do
    if [ -z "${!var}" ]; then
        echo "❌ Missing: $var"
    else
        echo "✓ Set: $var"
    fi
done
```

### Phase 3: Run Contract Tests

If `tests/test_contracts.py` or similar exists:

```bash
echo "=== Contract Tests ==="
pytest tests/test_contracts.py -v --tb=short 2>/dev/null || \
npm test -- --testPathPattern=contract 2>/dev/null || \
echo "No contract tests found"
```

### Phase 4: Run Integration Tests

```bash
echo "=== Integration Tests ==="
pytest tests/test_integration.py -v --tb=short 2>/dev/null || \
npm test -- --testPathPattern=integration 2>/dev/null || \
echo "No integration tests found"
```

### Phase 5: Startup Validation

If project has startup validation:

```bash
echo "=== Startup Validation ==="
# Python
python -c "from src.startup_validation import validate_startup_environment; validate_startup_environment()" 2>/dev/null || \

# Node
node -e "require('./src/startup-validation').validate()" 2>/dev/null || \

echo "No startup validation found (consider adding)"
```

### Phase 6: Documentation Verification

**CRITICAL**: Production deployments require complete documentation.

#### 6.1 Required Documentation Check

```bash
echo "=== Documentation Completeness ==="

# Check for required docs folders
REQUIRED_DOCS=(
    "docs/operations/runbooks"
    "docs/operations/playbooks"
    "docs/security"
    "docs/sre"
)

for doc_path in "${REQUIRED_DOCS[@]}"; do
    if [ -d "$doc_path" ] && [ "$(ls -A $doc_path 2>/dev/null)" ]; then
        echo "✓ $doc_path exists and has content"
    else
        echo "❌ $doc_path missing or empty"
    fi
done
```

#### 6.2 Critical Documentation Files

| Document | Required For | Status Check |
|----------|--------------|--------------|
| Deployment runbook | Any deploy | `docs/operations/runbooks/deployment.md` |
| Rollback runbook | Any deploy | `docs/operations/runbooks/rollback.md` |
| Incident playbook | Production | `docs/operations/playbooks/incident-response.md` |
| On-call guide | Production | `docs/operations/on-call.md` |
| SLO definitions | Production | `docs/sre/slo-definitions.md` |
| Monitoring docs | Production | `docs/sre/monitoring.md` |
| Threat model | Production | `docs/security/threat-model.md` |

```bash
echo "=== Critical Documentation ==="

# For ANY deployment
REQUIRED_FOR_DEPLOY=(
    "docs/operations/runbooks/deployment.md:Deployment runbook"
    "docs/operations/runbooks/rollback.md:Rollback runbook"
)

# For PRODUCTION deployment
REQUIRED_FOR_PROD=(
    "docs/operations/playbooks/incident-response.md:Incident playbook"
    "docs/operations/on-call.md:On-call guide"
    "docs/sre/slo-definitions.md:SLO definitions"
    "docs/sre/monitoring.md:Monitoring documentation"
    "docs/security/threat-model.md:Threat model"
)

for item in "${REQUIRED_FOR_DEPLOY[@]}"; do
    path="${item%%:*}"
    name="${item##*:}"
    if [ -f "$path" ]; then
        echo "✓ $name"
    else
        echo "❌ BLOCKING: $name missing ($path)"
    fi
done

# If deploying to production, check additional docs
if [ "$DEPLOY_ENV" = "production" ] || [ "$1" = "--production" ]; then
    echo ""
    echo "=== Production-Required Documentation ==="
    for item in "${REQUIRED_FOR_PROD[@]}"; do
        path="${item%%:*}"
        name="${item##*:}"
        if [ -f "$path" ]; then
            echo "✓ $name"
        else
            echo "❌ BLOCKING: $name missing ($path)"
        fi
    done
fi
```

#### 6.3 Documentation Freshness

```bash
echo "=== Documentation Freshness ==="

# Check if docs are older than 90 days
STALE_THRESHOLD=$((90 * 24 * 60 * 60))  # 90 days in seconds
NOW=$(date +%s)

for doc in docs/operations/runbooks/*.md docs/sre/*.md; do
    if [ -f "$doc" ]; then
        DOC_TIME=$(stat -f %m "$doc" 2>/dev/null || stat -c %Y "$doc" 2>/dev/null)
        AGE=$((NOW - DOC_TIME))
        if [ $AGE -gt $STALE_THRESHOLD ]; then
            echo "⚠ STALE: $doc ($(($AGE / 86400)) days old)"
        fi
    fi
done

# Check for TODOs in critical docs
if grep -r "TODO\|FIXME\|TBD" docs/operations/ docs/sre/ docs/security/ 2>/dev/null; then
    echo "⚠ Incomplete markers found in critical documentation"
fi
```

#### 6.4 API Documentation Sync

```bash
echo "=== API Documentation ==="

# Check OpenAPI spec is valid
if [ -f "docs/api/reference/openapi.yaml" ]; then
    npx @redocly/cli lint docs/api/reference/openapi.yaml 2>/dev/null && \
    echo "✓ OpenAPI spec is valid" || \
    echo "❌ OpenAPI spec has errors"
fi

# Check API changelog has recent entries
if [ -f "docs/api/changelog.md" ]; then
    LAST_ENTRY=$(grep -m1 "^## \[" docs/api/changelog.md | head -1)
    echo "✓ API Changelog last entry: $LAST_ENTRY"
fi
```

#### 6.5 Compliance Documentation

For regulated deployments:

```bash
echo "=== Compliance Documentation ==="

COMPLIANCE_DOCS=(
    "docs/security/compliance/soc2-mapping.md:SOC 2 mapping"
    "docs/security/compliance/gdpr-mapping.md:GDPR mapping"
    "docs/security/access-control.md:Access control matrix"
)

for item in "${COMPLIANCE_DOCS[@]}"; do
    path="${item%%:*}"
    name="${item##*:}"
    if [ -f "$path" ]; then
        echo "✓ $name"
    else
        echo "○ $name not found (may not be required)"
    fi
done
```

### Phase 7: Lessons Checklist

Review each prevention item from lessons. Output checklist:

**Authentication & Identity** (from lessons)
- [ ] Tested with REAL auth provider IDs (not mock UUIDs)
- [ ] Credential format matches deployment platform
- [ ] Auth headers pass through proxy/CDN

**Database** (from lessons)
- [ ] ID column types match auth provider format
- [ ] Migrations run separately from app startup
- [ ] Connection string verified

**API Contracts** (from lessons)
- [ ] Frontend/backend IDs match (contract test)
- [ ] Error responses are structured and displayed
- [ ] CORS configured for production domain

**Payments** (if applicable, from lessons)
- [ ] Webhook URL registered in dashboard
- [ ] Webhook handler is transactional
- [ ] Test vs live mode keys verified

### Phase 8: Generate Report

**All Checks Pass:**
```
╔════════════════════════════════════════════════════════════╗
║                 DEPLOYMENT READY ✓                         ║
╠════════════════════════════════════════════════════════════╣
║ TESTS                                                      ║
║   Contract Tests: ✓ 5/5 passed                             ║
║   Integration:    ✓ 8/8 passed                             ║
║   Startup:        ✓ Validation passed                      ║
╠════════════════════════════════════════════════════════════╣
║ ENVIRONMENT                                                ║
║   Variables:      ✓ All required vars set                  ║
║   Credentials:    ✓ Format validated                       ║
╠════════════════════════════════════════════════════════════╣
║ DOCUMENTATION                                              ║
║   Operations:     ✓ Runbooks present and current           ║
║   Security:       ✓ Threat model up to date                ║
║   SRE:            ✓ SLOs defined, monitoring documented    ║
║   API:            ✓ OpenAPI valid, changelog current       ║
╠════════════════════════════════════════════════════════════╣
║ LESSONS                                                    ║
║   Checklist:      ✓ 12/12 items verified                   ║
╠════════════════════════════════════════════════════════════╣
║ Ready to deploy!                                           ║
║                                                            ║
║ After deploy, run smoke tests:                             ║
║   ./scripts/smoke-test.sh production                       ║
╚════════════════════════════════════════════════════════════╝
```

**Issues Found:**
```
╔════════════════════════════════════════════════════════════╗
║                 DEPLOYMENT BLOCKED ✗                       ║
╠════════════════════════════════════════════════════════════╣
║ BLOCKING ISSUES                                            ║
║                                                            ║
║ ❌ Documentation: Rollback runbook missing                 ║
║    Create: docs/operations/runbooks/rollback.md            ║
║    Run: /project:docs operations                           ║
║                                                            ║
║ ❌ Contract Tests: 1 failure                               ║
║    - test_plan_ids_match: 'pack_10' not in backend         ║
╠════════════════════════════════════════════════════════════╣
║ WARNINGS (should fix, not blocking)                        ║
║                                                            ║
║ ⚠️  docs/sre/monitoring.md is 95 days old                  ║
║ ⚠️  No integration tests for Firebase UIDs                 ║
║    (See LESSON: Firebase UID ≠ UUID)                       ║
║ ⚠️  TODO found in docs/operations/runbooks/deployment.md   ║
╠════════════════════════════════════════════════════════════╣
║ Fix blocking issues before deploying                       ║
╚════════════════════════════════════════════════════════════╝
```

### Phase 9: Documentation Gate

If documentation is incomplete:

```
╔════════════════════════════════════════════════════════════╗
║              DOCUMENTATION GATE FAILED                     ║
╠════════════════════════════════════════════════════════════╣
║ Missing critical documentation for production deploy:      ║
║                                                            ║
║ Operations (required):                                     ║
║   ❌ docs/operations/runbooks/deployment.md                ║
║   ❌ docs/operations/runbooks/rollback.md                  ║
║   ❌ docs/operations/playbooks/incident-response.md        ║
║                                                            ║
║ SRE (required for production):                             ║
║   ❌ docs/sre/slo-definitions.md                           ║
║   ❌ docs/sre/monitoring.md                                ║
║                                                            ║
║ Quick fix:                                                 ║
║   /project:docs operations   - Generate operations docs    ║
║   /project:docs sre          - Generate SRE docs           ║
╚════════════════════════════════════════════════════════════╝
```

## Arguments

$ARGUMENTS

- `--skip-tests`: Only check environment and docs, skip tests
- `--skip-docs`: Skip documentation checks (NOT RECOMMENDED)
- `--production`: Apply stricter production requirements
- `--staging`: Apply staging-level checks
- `--verbose`: Show all checks, not just failures
- `--fix`: Attempt to fix common issues
- `--docs-only`: Only run documentation verification
