# Security Patterns (OWASP)

> Security best practices based on OWASP Top 10.
> Auto-discovered when security-related code detected.

## OWASP Top 10 (2021)

### 1. Broken Access Control

**Vulnerability**: Users can act outside their intended permissions.

```python
# BAD - No authorization check
@app.get("/api/users/{user_id}")
def get_user(user_id: str):
    return db.get_user(user_id)  # Anyone can view any user!

# GOOD - Check authorization
@app.get("/api/users/{user_id}")
def get_user(user_id: str, current_user: User = Depends(get_current_user)):
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(403, "Not authorized")
    return db.get_user(user_id)
```

**Prevention Checklist**:
- [ ] Deny by default
- [ ] Check authorization on EVERY request
- [ ] Use role-based access control (RBAC)
- [ ] Log access control failures

### 2. Cryptographic Failures

**Vulnerability**: Sensitive data exposed due to weak crypto.

```python
# BAD - Storing passwords in plain text
user.password = request.password

# GOOD - Hash passwords
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
user.password_hash = pwd_context.hash(request.password)

# BAD - Weak encryption
from Crypto.Cipher import DES  # Don't use DES!

# GOOD - Strong encryption
from cryptography.fernet import Fernet
key = Fernet.generate_key()
cipher = Fernet(key)
encrypted = cipher.encrypt(data)
```

**Prevention Checklist**:
- [ ] Use bcrypt/argon2 for passwords
- [ ] Use TLS 1.3 for data in transit
- [ ] Use AES-256 for data at rest
- [ ] Never commit secrets to git
- [ ] Rotate keys regularly

### 3. Injection

**Vulnerability**: Untrusted data sent to interpreter.

```python
# BAD - SQL Injection
query = f"SELECT * FROM users WHERE id = '{user_id}'"
db.execute(query)

# GOOD - Parameterized queries
query = "SELECT * FROM users WHERE id = %s"
db.execute(query, (user_id,))

# GOOD - ORM
user = User.query.filter_by(id=user_id).first()

# BAD - Command injection
os.system(f"convert {filename} output.png")

# GOOD - Use subprocess with list
subprocess.run(["convert", filename, "output.png"], check=True)
```

**Prevention Checklist**:
- [ ] Use parameterized queries ALWAYS
- [ ] Use ORM when possible
- [ ] Validate and sanitize all input
- [ ] Never build commands with string concatenation

### 4. Insecure Design

**Vulnerability**: Missing security controls in design.

```
Design Phase Security Questions:
┌─────────────────────────────────────────────────────────────┐
│ 1. What could go wrong? (Threat modeling)                  │
│ 2. What's the blast radius if compromised?                 │
│ 3. What data needs protection?                              │
│ 4. Who should have access to what?                          │
│ 5. What happens if a dependency is compromised?             │
└─────────────────────────────────────────────────────────────┘
```

**Prevention Checklist**:
- [ ] Threat model during design
- [ ] Principle of least privilege
- [ ] Defense in depth
- [ ] Secure by default

### 5. Security Misconfiguration

**Vulnerability**: Insecure default settings.

```yaml
# BAD - Debug mode in production
DEBUG: true
ALLOWED_HOSTS: ["*"]

# GOOD - Secure production config
DEBUG: false
ALLOWED_HOSTS: ["myapp.com", "www.myapp.com"]
SECURE_BROWSER_XSS_FILTER: true
SECURE_CONTENT_TYPE_NOSNIFF: true
X_FRAME_OPTIONS: "DENY"
SECURE_HSTS_SECONDS: 31536000
```

```python
# Security headers middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response
```

### 6. Vulnerable Components

**Vulnerability**: Using components with known vulnerabilities.

```bash
# Check for vulnerabilities
npm audit                    # Node.js
pip-audit                    # Python
bundle audit                 # Ruby
snyk test                    # Multi-language

# Auto-fix where possible
npm audit fix
```

**Prevention Checklist**:
- [ ] Run `npm audit` / `pip-audit` in CI
- [ ] Keep dependencies updated
- [ ] Remove unused dependencies
- [ ] Use Dependabot/Renovate

### 7. Authentication Failures

```python
# Secure authentication patterns

# 1. Rate limiting
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@app.post("/login")
@limiter.limit("5/minute")
async def login(request: Request):
    ...

# 2. Secure session handling
SESSION_CONFIG = {
    "secret_key": os.environ["SESSION_SECRET"],  # From env
    "cookie_httponly": True,
    "cookie_secure": True,  # HTTPS only
    "cookie_samesite": "Lax",
    "permanent_session_lifetime": timedelta(hours=1),
}

# 3. Multi-factor authentication
def verify_mfa(user, code):
    totp = pyotp.TOTP(user.mfa_secret)
    return totp.verify(code, valid_window=1)

# 4. Password requirements
def validate_password(password):
    if len(password) < 12:
        raise ValueError("Password must be at least 12 characters")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain uppercase")
    if not re.search(r"[a-z]", password):
        raise ValueError("Password must contain lowercase")
    if not re.search(r"\d", password):
        raise ValueError("Password must contain number")
```

### 8. Data Integrity Failures

```python
# Verify data integrity

# 1. Sign sensitive data
import hmac
import hashlib

def sign_data(data: str, secret: str) -> str:
    return hmac.new(
        secret.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()

def verify_signature(data: str, signature: str, secret: str) -> bool:
    expected = sign_data(data, secret)
    return hmac.compare_digest(signature, expected)

# 2. Verify webhooks
@app.post("/webhook")
async def webhook(request: Request):
    signature = request.headers.get("X-Signature")
    body = await request.body()

    if not verify_signature(body, signature, WEBHOOK_SECRET):
        raise HTTPException(401, "Invalid signature")
```

### 9. Logging & Monitoring Failures

```python
# Comprehensive security logging

import structlog

logger = structlog.get_logger()

# Log security events
logger.warning("auth.failed",
    user_id=user_id,
    ip=request.client.host,
    reason="invalid_password",
    attempt_count=attempts
)

logger.info("auth.success",
    user_id=user_id,
    ip=request.client.host,
    mfa_used=True
)

logger.critical("security.breach_attempt",
    user_id=user_id,
    action="privilege_escalation",
    ip=request.client.host
)

# What to log:
# - Authentication attempts (success/failure)
# - Authorization failures
# - Input validation failures
# - API rate limit hits
# - Admin actions
# - Data exports
```

### 10. Server-Side Request Forgery (SSRF)

```python
# BAD - User-controlled URL
@app.post("/fetch")
def fetch_url(url: str):
    return requests.get(url).text  # Can access internal services!

# GOOD - Validate and restrict URLs
ALLOWED_HOSTS = ["api.example.com", "cdn.example.com"]

def is_url_allowed(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in ["http", "https"]:
        return False
    if parsed.hostname not in ALLOWED_HOSTS:
        return False
    # Block internal IPs
    try:
        ip = socket.gethostbyname(parsed.hostname)
        if ipaddress.ip_address(ip).is_private:
            return False
    except socket.gaierror:
        return False
    return True

@app.post("/fetch")
def fetch_url(url: str):
    if not is_url_allowed(url):
        raise HTTPException(400, "URL not allowed")
    return requests.get(url, timeout=5).text
```

## Security Checklist

```markdown
## Pre-Deploy Security Checklist

### Authentication
- [ ] Passwords hashed with bcrypt/argon2
- [ ] Rate limiting on auth endpoints
- [ ] Session cookies HttpOnly + Secure
- [ ] CSRF protection enabled

### Authorization
- [ ] Every endpoint checks permissions
- [ ] Principle of least privilege
- [ ] Admin actions logged

### Data Protection
- [ ] TLS everywhere
- [ ] Sensitive data encrypted at rest
- [ ] No secrets in code/git
- [ ] PII handling documented

### Input Validation
- [ ] All input validated
- [ ] Parameterized queries only
- [ ] File uploads validated

### Headers
- [ ] CSP header set
- [ ] HSTS enabled
- [ ] X-Frame-Options: DENY

### Dependencies
- [ ] npm audit / pip-audit clean
- [ ] No known vulnerabilities

### Logging
- [ ] Security events logged
- [ ] No sensitive data in logs
- [ ] Alerts configured
```
