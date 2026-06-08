# Security Best Practices

Comprehensive security hardening guide for the Controle Financeiro application covering implementation details and operational recommendations.

## 1. Authentication & Authorization

### JWT Token Management

**Implementation**:
- Tokens signed with HS256 algorithm using 32+ character secret key
- Token lifetime: 1 hour (configurable via `JWT_EXPIRATION_HOURS`)
- Tokens stored in Authorization header: `Authorization: Bearer <token>`
- No token rotation on refresh (consider implementing for higher security)

**Best Practices**:
```python
# ✅ DO: Validate token expiration
if token_payload['exp'] < time.time():
    raise InvalidTokenError()

# ❌ DON'T: Accept expired tokens
# ❌ DON'T: Log tokens in debug output
```

**Configuration**:
```env
JWT_SECRET_KEY=<generate-with-openssl-rand-base64-32>
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=1
```

### Password Security

**Requirements**:
- Minimum 8 characters (enforced by Pydantic validation)
- Hashed with Bcrypt (cost factor 12)
- Never logged or displayed in responses
- Changed via dedicated endpoint with old password verification

**Implementation**:
```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hash password
hashed = pwd_context.hash(password)

# Verify password
is_valid = pwd_context.verify(password, hashed)
```

**Bcrypt Cost Factor 12**:
- ~100ms per hash attempt on modern hardware
- Makes brute force attacks 100x more expensive than cost factor 10
- Balance between security and user experience

---

## 2. CSRF Protection

### Double-Submit Cookie Pattern

**How It Works**:
1. Server generates CSRF token on GET requests
2. Token sent in secure HttpOnly cookie (can't be read by JavaScript)
3. Client must include same token in `X-CSRF-Token` header
4. Server validates header token matches cookie token
5. XSS attacker can't read token from cookie → can't add header
6. Cross-site form submission can't add custom header → blocked by CORS

**Protected Methods**: POST, PUT, PATCH, DELETE

**Exempt Paths** (don't require CSRF):
```python
EXEMPT_PATHS = {
    "/api/auth/login",
    "/api/auth/register",
    "/api/auth/logout",
    "/health",
    "/docs",
}
```

**Token Structure**:
```
timestamp|random_bytes|hmac_signature

Example: 2024-06-08T10:30:45.123456|base64_random_32_bytes|sha256_hmac_hex
```

**Validation Steps**:
1. Token has 3 pipe-separated parts
2. HMAC signature valid (prevents tampering)
3. Token not older than 24 hours
4. Header token matches cookie token exactly

**Frontend Implementation**:
```javascript
// Get CSRF token from cookie
const csrfToken = document.cookie
  .split('; ')
  .find(row => row.startsWith('csrf_token='))
  ?.split('=')[1];

// Include in request headers
fetch('/api/payments', {
  method: 'POST',
  headers: {
    'X-CSRF-Token': csrfToken,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(data)
});
```

**Cookie Attributes**:
- `HttpOnly`: Prevent JavaScript access (XSS protection)
- `Secure`: HTTPS only (production)
- `SameSite=Strict`: Never send on cross-site requests
- `Max-Age`: 24 hours
- `Path`: `/`

---

## 3. Rate Limiting

### Token Bucket Algorithm

**Implemented Limits**:

| Endpoint | Limit | Window | Purpose |
|----------|-------|--------|---------|
| Login | 5 requests | 10 minutes | Prevent brute force |
| Register | 3 requests | 1 hour | Prevent spam |
| API General | 100 requests | 1 minute | DoS protection |
| API Strict | 10 requests | 1 minute | Sensitive operations |

**How Token Bucket Works**:
```
Initial tokens: 5 (for login)
Refill rate: 0.5 tokens/minute (1 token per 2 minutes)

Timeline:
  T=0:00   - Attempt 1 ✓ (4 tokens left)
  T=0:00   - Attempt 2 ✓ (3 tokens left)
  T=0:00   - Attempt 3 ✓ (2 tokens left)
  T=0:00   - Attempt 4 ✓ (1 token left)
  T=0:00   - Attempt 5 ✓ (0 tokens left)
  T=0:00   - Attempt 6 ✗ (rate limited)
  T=2:00   - Refilled 1 token
  T=2:00   - Attempt 6 ✓ (0 tokens left)
  T=4:00   - Refilled 1 token
  T=4:00   - Attempt 7 ✓
```

**Response on Rate Limit**:
```json
HTTP/1.1 429 Too Many Requests
Retry-After: 45

{
  "detail": "Too many login attempts. Please try again in 45 seconds."
}
```

**Implementation**:
```python
from app.utils.rate_limit import get_rate_limiter

limiter = get_rate_limiter()
if not limiter.is_allowed("login", client_ip):
    raise HTTPException(status_code=429, detail="Rate limited")
```

**Client-Side Handling**:
```javascript
async function login(username, password) {
  try {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password })
    });

    if (response.status === 429) {
      const retryAfter = response.headers.get('Retry-After');
      showError(`Rate limited. Retry after ${retryAfter} seconds`);
      return;
    }
    // ...
  } catch (error) {
    // Handle error
  }
}
```

---

## 4. Security Headers

### Implemented Headers

**X-Frame-Options: SAMEORIGIN**
- Prevents clickjacking attacks
- Allows embedding only from same origin
- Prevents framing in malicious sites

**X-Content-Type-Options: nosniff**
- Forces browser to respect Content-Type header
- Prevents MIME type sniffing attacks
- Prevents JavaScript execution in HTML contexts

**X-XSS-Protection: 1; mode=block**
- Enables XSS protection in older browsers
- Blocks page if XSS detected
- Modern browsers use CSP instead

**Content-Security-Policy**:
```
default-src 'self';              # Only self by default
script-src 'self' 'unsafe-inline';  # Allow inline scripts (for Vue)
style-src 'self' 'unsafe-inline';   # Allow inline styles (for Tailwind)
img-src 'self' data: https:;     # Allow images from self, data URLs, HTTPS
font-src 'self';                 # Allow fonts from self
connect-src 'self';              # API calls to self only
frame-ancestors 'self';          # Only embed in same origin
```

**Strict-Transport-Security (HSTS)** - Production Only:
```
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload

- max-age=31536000: Enforce HTTPS for 1 year
- includeSubDomains: Include all subdomains
- preload: Add to browser's HSTS preload list
```

**X-DNS-Prefetch-Control: off**
- Disables DNS prefetching for privacy
- Prevents information leakage about visited domains

**Referrer-Policy: strict-origin-when-cross-origin**
- Send full referrer only for same-site navigation
- Send origin only for cross-site navigation
- Never send referrer for HTTP to HTTPS

---

## 5. Multi-Tenancy & Data Isolation

### User ID Filtering

**Architecture**:
- Every data table includes `user_id` column
- All queries filter by `user_id` from JWT token
- Prevents accidental or intentional data leakage

**Implementation Pattern**:
```python
@router.get("/api/accounts")
async def list_accounts(user_id: str = Depends(get_current_user), db: Session = Depends(get_db)):
    # CRITICAL: Always filter by user_id
    accounts = db.query(Account).filter(Account.user_id == user_id).all()
    return accounts

# ❌ WRONG: Missing user_id filter
# accounts = db.query(Account).all()  # Returns all users' accounts!
```

**Database Constraints**:
```sql
-- Enforce user_id cannot be NULL
ALTER TABLE accounts ADD CONSTRAINT accounts_user_id_not_null
  CHECK (user_id IS NOT NULL);

-- Create indexes for filtering
CREATE INDEX idx_accounts_user_id ON accounts(user_id);
CREATE INDEX idx_payments_user_id ON payments(user_id);
```

**Auditing User Access**:
```python
# Log suspicious queries
if user_id != requested_user_id:
    logger.warning(f"User {user_id} attempted to access data for {requested_user_id}")
    raise PermissionError()
```

---

## 6. Input Validation & XSS Prevention

### Pydantic Validation

**Automatic Validation**:
```python
from pydantic import BaseModel, Field, EmailStr

class PaymentCreate(BaseModel):
    description: str = Field(..., min_length=1, max_length=255)
    amount: float = Field(..., gt=0)
    is_paid: bool = False
    email: EmailStr  # Validates email format

# Automatically validates:
# - description: non-empty string, max 255 chars
# - amount: positive number
# - email: valid email format
```

**Stored XSS Prevention**:
- All string inputs sanitized automatically by Pydantic
- Database stores actual strings, not HTML/JavaScript
- Frontend escapes when displaying (Vue.js automatic)

**Reflected XSS Prevention**:
- All API responses use JSON (not HTML)
- Custom error messages don't include user input

**Example**:
```python
# ❌ WRONG: User input in response
return {"error": f"User {user_input} not found"}

# ✅ CORRECT: Sanitized response
return {"error": "User not found"}
```

---

## 7. SQL Injection Prevention

### SQLAlchemy ORM

**Never use raw SQL with string concatenation**:
```python
# ❌ VULNERABLE: SQL Injection
query = f"SELECT * FROM accounts WHERE id = {account_id}"
db.execute(query)

# ✅ SAFE: Parameterized query with ORM
account = db.query(Account).filter(Account.id == account_id).first()

# ✅ SAFE: If raw SQL needed, use parameterized query
account = db.execute(
    text("SELECT * FROM accounts WHERE id = :id"),
    {"id": account_id}
).first()
```

**All endpoints use ORM exclusively** - SQLAlchemy generates safe parameterized queries automatically.

---

## 8. Secure Configuration

### Environment Variables

**Never commit secrets**:
```bash
# ✅ DO
JWT_SECRET_KEY=auto_generated_random_string_32_chars_min
DATABASE_URL=sqlite:////data/controle_financeiro.db

# ❌ DON'T
JWT_SECRET_KEY=hardcoded_secret_in_code
JWT_SECRET_KEY=default_dev_key_123
```

**Generate JWT Secret**:
```bash
# Option 1: Python
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Option 2: OpenSSL
openssl rand -base64 32

# Result: 32+ character random string
```

**File Permissions**:
```bash
# .env should be readable only by app user
chmod 600 .env

# Database file should be readable/writable only by app user
chmod 600 /data/controle_financeiro.db

# Logs should not be world-readable (may contain sensitive data)
chmod 640 /var/log/controle-financeiro.log
```

### Sensitive Configuration

```env
# PRODUCTION ONLY
ENVIRONMENT=production
JWT_SECRET_KEY=<generate-new-for-each-environment>
CORS_ORIGINS=https://yourdomain.com
DATABASE_URL=sqlite:////data/controle_financeiro.db
LOG_LEVEL=WARNING  # Don't log debug info in production
SQLALCHEMY_ECHO=false  # Don't log SQL queries
```

---

## 9. API Security

### Endpoint Protection

**GET endpoints** - Public (no authentication required):
```
GET /health - Server health check
GET /docs - API documentation
GET /openapi.json - OpenAPI schema
```

**POST endpoints** - Require authentication:
```
POST /api/auth/login - Login (rate limited, no auth required)
POST /api/auth/register - Register (rate limited, no auth required)
POST /api/accounts - Create account (authentication required)
POST /api/payments - Create payment (authentication required)
```

**Protected Endpoint Pattern**:
```python
@router.post("/api/accounts")
async def create_account(
    account: AccountCreate,
    user_id: str = Depends(get_current_user),  # Requires JWT token
    db: Session = Depends(get_db),
):
    # user_id extracted from token
    account.user_id = user_id
    return AccountService.create(db, account)
```

### Error Messages

**Safe Error Messages** - Don't leak information:
```python
# ❌ UNSAFE: Reveals which field failed
raise HTTPException(
    status_code=400,
    detail="Email already exists in database"
)

# ✅ SAFE: Generic message
raise HTTPException(
    status_code=400,
    detail="User already exists"
)
```

**Exception Handlers**:
```python
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")  # Log full error
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},  # Generic response
    )
```

---

## 10. Docker Security

### Running Non-Root

**Dockerfile**:
```dockerfile
RUN useradd -m -u 1000 appuser
USER appuser
```

**Benefits**:
- Limits damage if container is compromised
- Prevents container escape to host root
- Follows principle of least privilege

### Image Scanning

```bash
# Scan for vulnerabilities
docker scan controle-financeiro-backend

# Update base images regularly
FROM python:3.11-slim  # Get latest patches
```

### Secrets Management

**Never embed secrets in image**:
```dockerfile
# ❌ WRONG
ENV JWT_SECRET_KEY=hardcoded_value

# ✅ CORRECT
# Pass via environment file or Docker Compose
```

---

## 11. Operational Security

### Logging & Monitoring

**What to Log**:
```python
# ✅ DO LOG
logger.info(f"User {user_id} logged in from {client_ip}")
logger.warning(f"Failed login attempt from {client_ip}")
logger.error(f"Database connection failed: {error}")

# ❌ DON'T LOG
logger.debug(f"User password: {password}")  # Never log passwords
logger.debug(f"JWT token: {token}")  # Never log tokens
logger.debug(f"Database URL: {DATABASE_URL}")  # May contain credentials
```

**Log Retention**:
- Keep 30 days of logs (balance security vs storage)
- Rotate logs daily (prevents huge single files)
- Monitor for suspicious patterns (brute force, injections)

### Regular Updates

**Dependencies**:
```bash
# Check for vulnerabilities monthly
pip install --upgrade -r requirements.txt
npm update

# Review security advisories
pip-audit  # For Python packages
npm audit  # For Node packages
```

**Database Backups**:
```bash
# Daily automated backups
docker exec controle-financeiro-backend \
  sqlite3 /data/controle_financeiro.db ".backup '/backups/db_$(date +%Y%m%d_%H%M%S).db'"

# Test restore process quarterly
```

### Firewall Rules

**Allowed Ports** (production):
```bash
sudo ufw allow 22/tcp   # SSH for management
sudo ufw allow 80/tcp   # HTTP (redirect to HTTPS)
sudo ufw allow 443/tcp  # HTTPS
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw enable
```

**Block Ports** (no access needed):
- 3000-9999 (development ports)
- 5432 (PostgreSQL)
- 27017 (MongoDB)
- 3306 (MySQL)

---

## 12. Security Checklist

### Before Deployment

- [ ] JWT_SECRET_KEY changed to 32+ character random string
- [ ] CORS_ORIGINS set to actual domain (not localhost)
- [ ] ENVIRONMENT=production
- [ ] LOG_LEVEL=WARNING (not DEBUG)
- [ ] SQLALCHEMY_ECHO=false
- [ ] Database file has secure permissions (chmod 600)
- [ ] .env file has secure permissions (chmod 600)
- [ ] HTTPS/TLS certificate installed
- [ ] SSL certificate from Let's Encrypt (auto-renewal configured)
- [ ] Rate limiting configured and tested
- [ ] CSRF protection enabled
- [ ] Security headers present in responses
- [ ] Password reset functionality requires email verification
- [ ] Database backups automated and tested
- [ ] WAF (Web Application Firewall) configured
- [ ] DDoS protection enabled (Cloudflare, AWS Shield, etc.)
- [ ] Security monitoring/alerting in place
- [ ] Incident response plan documented
- [ ] Penetration testing completed
- [ ] Dependencies scanned for vulnerabilities
- [ ] Firewall rules restricting access to needed ports only

### Regular Maintenance

- [ ] Check logs daily for suspicious activity
- [ ] Update dependencies monthly
- [ ] Rotate database backups (keep 30 days)
- [ ] Review access logs for unauthorized attempts
- [ ] Test database restore process quarterly
- [ ] Conduct security audit annually

---

## 13. Incident Response

### If Compromised

1. **Immediate Actions** (within 1 hour):
   - Revoke all JWT tokens (change JWT_SECRET_KEY)
   - Force password reset for all users
   - Backup database (preserve evidence)
   - Review recent logs for unauthorized access
   - Rotate database credentials

2. **Investigation** (within 24 hours):
   - Identify affected users and data
   - Determine attack vector
   - Check for data exfiltration
   - Review firewall logs
   - Scan for backdoors/persistence

3. **Communication** (within 72 hours):
   - Notify affected users
   - Disclose data breach if applicable
   - Document incident report
   - File regulatory reports if required

### Password Reset After Breach

```python
# Force all users to reset password on next login
def force_password_reset(user_id: str, db: Session):
    user = db.query(User).filter(User.id == user_id).first()
    user.password_reset_required = True
    user.last_reset_timestamp = datetime.utcnow()
    db.commit()

# Check on every login
@router.post("/api/auth/login")
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    user, token = AuthService.login(db, request.username, request.password)
    if user.password_reset_required:
        raise HTTPException(
            status_code=403,
            detail="Password reset required. Please reset your password."
        )
```

---

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Bcrypt Best Practices](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
- [Content Security Policy](https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html)
- [CSRF Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)

---

**Last Updated**: June 2024
**Version**: 1.0.0
