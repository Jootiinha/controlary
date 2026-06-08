# Security Maintenance & Vulnerability Scanning

Comprehensive guide for ongoing security maintenance, dependency vulnerability scanning, and security updates for the Controle Financeiro application.

## 1. Dependency Vulnerability Scanning

### Python Dependencies

#### pip-audit (Recommended)

Actively maintained tool specifically for Python package vulnerabilities.

```bash
# Install
pip install pip-audit

# Scan for vulnerabilities
pip-audit

# Scan with detailed output
pip-audit --verbose

# Generate JSON report
pip-audit --format json > audit_report.json

# Check against specific advisory database
pip-audit --index https://pyup.io/safety/json

# Ignore known vulnerabilities (with justification)
pip-audit --ignore-ids CVE-2024-XXXX --ignore-ids PYUP-XXXX
```

**Output Example**:
```
Found 3 known security vulnerabilities in your dependency tree:
┌─────────────────────────────────────────────┬────────────────────────────┐
│ Package                                     │ Vulnerability              │
├─────────────────────────────────────────────┼────────────────────────────┤
│ fastapi (0.95.0)                            │ CVE-2024-XXXXX             │
│ Severity: HIGH                              │ Regular expression DoS     │
├─────────────────────────────────────────────┼────────────────────────────┤
│ jinja2 (3.0.0)                              │ CVE-2024-YYYYY             │
│ Severity: CRITICAL                          │ Code injection via template│
└─────────────────────────────────────────────┴────────────────────────────┘

Run `pip install --upgrade` to remediate vulnerabilities.
```

#### Safety (Alternative)

Older but widely used Python security vulnerability scanner.

```bash
# Install
pip install safety

# Scan
safety check

# Generate JSON
safety check --json > safety_report.json

# Scan with specific database
safety check --db https://safetydatabase.dev.fi/data
```

#### Requirements.txt

Keep dependencies pinned to specific versions for reproducibility:

```txt
# backend/requirements.txt
fastapi==0.104.1          # Web framework
uvicorn==0.24.0           # ASGI server
sqlalchemy==2.0.23        # ORM
pydantic==2.5.0           # Data validation
python-jose==3.3.0        # JWT tokens
passlib==1.7.4            # Password hashing
bcrypt==4.1.0             # Bcrypt implementation
python-multipart==0.0.6   # Form parsing
email-validator==2.1.0    # Email validation
pytest==7.4.3             # Testing
pytest-cov==4.1.0         # Coverage
```

**Best Practices**:
- Pin all dependencies to exact versions (avoid `~=`, `>=`)
- Use hash checking for reproducible builds
- Separate dev and production dependencies

```bash
# Split dependencies
pip freeze | grep -v "^-e" > requirements-prod.txt
pip freeze | grep "^pytest\|^black\|^mypy" > requirements-dev.txt
```

### Node.js Dependencies

#### npm audit

Built-in vulnerability scanner for Node packages.

```bash
# Check for vulnerabilities
npm audit

# Show detailed info
npm audit --detailed

# Generate JSON report
npm audit --json > npm_audit.json

# Fix automatically
npm audit fix

# Fix with major version updates
npm audit fix --force

# Set severity level
npm audit --audit-level=moderate  # moderate, high, critical
```

**Output Example**:
```
up to date, audited 287 packages in 2s

3 vulnerabilities

┌────────────────────────────────────────────────┬──────────┐
│ High                                           │ Count    │
├────────────────────────────────────────────────┼──────────┤
│ lodash                                         │ 1        │
│ Prototype pollution                            │          │
├────────────────────────────────────────────────┼──────────┤
│ vue                                            │ 2        │
│ XSS vulnerability in template parsing          │          │
└────────────────────────────────────────────────┴──────────┘

Run `npm audit fix` to fix 1 vulnerability
```

#### Snyk (Commercial Alternative)

More advanced vulnerability scanning with fix recommendations.

```bash
# Install
npm install -g snyk

# Test for vulnerabilities
snyk test

# Fix vulnerabilities
snyk fix

# Monitor for new vulnerabilities
snyk monitor
```

#### Dependabot (GitHub Integration)

Automated dependency updates with security scanning.

1. **Enable in GitHub**:
   - Go to repo Settings → Code security → Dependabot
   - Enable "Dependabot alerts"
   - Enable "Dependabot security updates"

2. **Configure** (create `.github/dependabot.yml`):
```yaml
version: 2
updates:
  - package-ecosystem: pip
    directory: "/backend"
    schedule:
      interval: daily
    allow:
      - dependency-type: "direct"
      - dependency-type: "indirect"
    reviewers:
      - "your-github-username"
    labels:
      - "dependencies"
      - "security"

  - package-ecosystem: npm
    directory: "/frontend"
    schedule:
      interval: daily
    allow:
      - dependency-type: "direct"
    reviewers:
      - "your-github-username"
    labels:
      - "dependencies"
      - "security"
```

---

## 2. Security Update Process

### When a Vulnerability is Found

**Step 1: Assess Severity** (within 1 hour)
```
Critical (CVSS 9-10):   Apply patch immediately
High (CVSS 7-8.9):      Apply patch within 1-2 days
Medium (CVSS 4-6.9):    Apply patch within 1 week
Low (CVSS 0-3.9):       Apply patch within 1 month
```

**Step 2: Test the Fix** (within 4 hours for critical)
```bash
# Create test branch
git checkout -b security/fix-cve-2024-XXXXX

# Update dependency
pip install --upgrade fastapi

# Run full test suite
pytest --cov=app tests/

# Check for breaking changes
pip install pipdeptree
pipdeptree -p fastapi

# For Node
npm update lodash
npm test
```

**Step 3: Deploy to Production** (ASAP for critical)
```bash
# 1. Merge to main branch
git push origin security/fix-cve-2024-XXXXX
# Create Pull Request

# 2. Code review and merge
# (skip manual review for critical security fixes)

# 3. Deploy
docker-compose build --no-cache
docker-compose up -d

# 4. Monitor
docker-compose logs -f backend
docker-compose logs -f frontend

# 5. Verify
curl https://yourdomain.com/health
```

### Automated Updates

Create a cron job for regular dependency checks:

```bash
# /usr/local/bin/check_vulnerabilities.sh
#!/bin/bash

cd /app/controle-financeiro

# Python
echo "=== Python Vulnerabilities ==="
python -m pip install pip-audit
pip-audit > /tmp/python_vulns.txt
if grep -q "known security vulnerabilities" /tmp/python_vulns.txt; then
  cat /tmp/python_vulns.txt | mail -s "Python Vulnerabilities Found" admin@yourdomain.com
fi

# Node
echo "=== Node Vulnerabilities ==="
cd frontend
npm audit > /tmp/node_vulns.txt 2>&1
if grep -q "vulnerabilities" /tmp/node_vulns.txt; then
  cat /tmp/node_vulns.txt | mail -s "Node Vulnerabilities Found" admin@yourdomain.com
fi
```

Add to crontab (run daily at 2 AM):
```bash
0 2 * * * /usr/local/bin/check_vulnerabilities.sh
```

---

## 3. Regular Security Audits

### Weekly Tasks (15 minutes)

```bash
# Check security alerts in logs
docker-compose logs backend | grep -i "security\|error\|failed\|unauthorized"

# Review audit logs
sqlite3 /data/controle_financeiro.db \
  "SELECT * FROM audit_logs WHERE created_at > datetime('now', '-7 days') AND status LIKE '%security%' OR status = 'failure';"

# Check failed login attempts
sqlite3 /data/controle_financeiro.db \
  "SELECT client_ip, COUNT(*) as attempts FROM audit_logs WHERE operation = 'login' AND status = 'failure' AND created_at > datetime('now', '-7 days') GROUP BY client_ip ORDER BY attempts DESC LIMIT 10;"
```

### Monthly Tasks (1 hour)

```bash
# 1. Dependency scanning
pip-audit --verbose
npm audit --detailed

# 2. Check for configuration drift
git diff config/production.env

# 3. Review user access logs
sqlite3 /data/controle_financeiro.db \
  "SELECT user_id, COUNT(*) as login_count FROM audit_logs WHERE operation = 'login' AND status = 'success' AND created_at > datetime('now', '-30 days') GROUP BY user_id ORDER BY login_count DESC;"

# 4. Database integrity check
sqlite3 /data/controle_financeiro.db "PRAGMA integrity_check;"

# 5. Test backup/restore process
docker cp controle-financeiro-backend:/data/controle_financeiro.db /tmp/test_backup.db
sqlite3 /tmp/test_backup.db ".tables"  # Verify backup validity
```

### Quarterly Tasks (2-3 hours)

- [ ] Full vulnerability scan (OWASP dependency-check)
- [ ] Penetration testing (hire external firm)
- [ ] Code review focusing on security
- [ ] Update security documentation
- [ ] Test disaster recovery procedures
- [ ] Review and update firewall rules
- [ ] Compliance audit (GDPR, etc.)

---

## 4. OWASP Dependency-Check

Comprehensive dependency scanning against multiple databases.

```bash
# Install
brew install dependency-check  # macOS
# or download from https://github.com/jeremylong/DependencyCheck

# Scan backend
dependency-check.sh --project "Controle Financeiro Backend" \
  --scan /path/to/backend \
  --format HTML \
  --out /tmp/backend_report.html

# Scan frontend
dependency-check.sh --project "Controle Financeiro Frontend" \
  --scan /path/to/frontend \
  --format HTML \
  --out /tmp/frontend_report.html

# Docker-based (no installation needed)
docker run --rm -e user=$USER \
  -v $(pwd):/src \
  -v $(pwd)/reports:/report \
  owasp/dependency-check:latest \
  --project "Controle Financeiro" \
  --scan /src \
  --format HTML \
  --out /report
```

**Output**: HTML report with CVEs, severity, and remediation advice

---

## 5. Container Image Scanning

Scan Docker images for base OS vulnerabilities.

### Trivy (Recommended)

```bash
# Install
brew install aquasecurity/trivy/trivy
# or
curl https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh

# Scan image
trivy image controle-financeiro-backend:latest

# Scan with severity filter
trivy image --severity HIGH,CRITICAL controle-financeiro-backend:latest

# Generate JSON report
trivy image --format json --output report.json controle-financeiro-backend:latest

# Scan Dockerfile
trivy config backend/Dockerfile

# Show fix recommendations
trivy image --format table --show-suppressed controle-financeiro-backend:latest
```

**Output Example**:
```
controle-financeiro-backend:latest (python:3.11-slim)

Total: 5 (UNKNOWN: 0, LOW: 2, MEDIUM: 3, HIGH: 0, CRITICAL: 0)

MEDIUM python-yaml https://avd.aquasec.com/nvd/cve-2021-20320
MEDIUM urllib3  https://avd.aquasec.com/nvd/cve-2023-45803
```

### Anchore (Alternative)

```bash
# Install
curl https://anchorectl.anchore.io/download/install.sh | bash

# Scan
anchore-cli image add controle-financeiro-backend:latest
anchore-cli image wait controle-financeiro-backend:latest
anchore-cli image vuln controle-financeiro-backend:latest all
```

---

## 6. Static Code Analysis

### Python

#### Bandit (Security-focused)

```bash
# Install
pip install bandit

# Scan backend
bandit -r app/ --format json -o bandit_report.json

# Specific checks
bandit -r app/ --tests B201,B301,B302,B303,B304,B305,B306

# Severity levels
bandit -r app/ --level MEDIUM --severity-level HIGH
```

**Output**: Lists security issues like hardcoded passwords, insecure deserialization, SQL injection, etc.

#### Pylint (Code quality)

```bash
# Install
pip install pylint

# Scan
pylint app/ --output-format=json > pylint_report.json

# Check specific security categories
pylint app/ --disable=all --enable=security
```

#### MyPy (Type checking)

```bash
# Install
pip install mypy

# Check types
mypy app/ --strict
```

### JavaScript/Node

#### ESLint (Code quality)

```bash
# Install
npm install eslint --save-dev
npm init @eslint/config

# Scan
npx eslint src/ --format json -o eslint_report.json

# Security plugin
npm install eslint-plugin-security --save-dev
```

#### SonarJS (Security analysis)

```bash
# Install
npm install sonarjs --save-dev

# Scan
npx sonarjs src/
```

---

## 7. License Compliance

Ensure dependencies don't have restrictive licenses.

### Python

```bash
# Install
pip install pip-licenses

# Check licenses
pip-licenses

# Fail on restricted licenses
pip-licenses --format=csv --with-urls | grep -E "AGPL|SSPL"
```

### Node

```bash
# Install
npm install -g license-check-and-gather

# Check
license-check-and-gather

# Ignore specific licenses
license-check-and-gather --ignore "MIT,Apache-2.0"
```

---

## 8. Security Compliance

### OWASP Top 10 (2023) Checklist

- [ ] **A01:2021 – Broken Access Control**
  - Enforce user_id filtering in all queries
  - Validate authorization on every endpoint
  - Use least privilege principle

- [ ] **A02:2021 – Cryptographic Failures**
  - Use HTTPS/TLS in production
  - Bcrypt password hashing (cost 12)
  - Secure random token generation
  - Never log passwords/tokens

- [ ] **A03:2021 – Injection**
  - Use SQLAlchemy ORM (never raw SQL)
  - Validate all inputs with Pydantic
  - Parameterized queries always

- [ ] **A04:2021 – Insecure Design**
  - Rate limiting on auth endpoints
  - CSRF protection on state-changing operations
  - Input validation on all boundaries

- [ ] **A05:2021 – Security Misconfiguration**
  - No debug mode in production
  - Secrets not in code/config files
  - Security headers enabled
  - Least privilege on files/directories

- [ ] **A06:2021 – Vulnerable and Outdated Components**
  - Regular dependency scanning
  - Automated security updates
  - Remove unused dependencies

- [ ] **A07:2021 – Identification and Authentication Failures**
  - Strong password requirements
  - Rate limiting on login (5 attempts/10min)
  - Multi-factor authentication (future)
  - Session timeout on logout

- [ ] **A08:2021 – Software and Data Integrity Failures**
  - Code review before deployment
  - Signed commits (GPG)
  - Automated test suite
  - Secure CI/CD pipeline

- [ ] **A09:2021 – Logging and Monitoring Failures**
  - Audit log all sensitive operations
  - Alert on security events
  - Log centralization
  - Retain logs 30+ days

- [ ] **A10:2021 – Server-Side Request Forgery**
  - Validate URLs/IPs
  - Whitelist allowed destinations
  - Disable redirects to untrusted hosts

### GDPR Compliance (if applicable)

- [ ] User data encryption at rest
- [ ] Secure data deletion (GDPR right to be forgotten)
- [ ] Data access logging (audit trail)
- [ ] Data breach notification process
- [ ] Privacy policy updated
- [ ] Data processing agreements in place

---

## 9. Incident Response

### Security Incident Checklist

**Immediate (0-1 hour)**:
```bash
# 1. Isolate affected systems
docker-compose down backend  # If backend compromised

# 2. Preserve evidence
docker cp controle-financeiro-backend:/data /tmp/incident_backup_$(date +%s)
docker logs controle-financeiro-backend > /tmp/backend_logs_$(date +%s).txt

# 3. Review recent logs
grep "security_event\|rate_limit\|unauthorized" /tmp/backend_logs*.txt

# 4. Identify scope
sqlite3 /data/controle_financeiro.db \
  "SELECT * FROM audit_logs WHERE created_at > datetime('now', '-1 hour') AND status = 'security_event';"
```

**Short-term (1-24 hours)**:
- [ ] Change JWT_SECRET_KEY (force re-login)
- [ ] Force password reset for affected users
- [ ] Review database backups
- [ ] Check for data exfiltration
- [ ] Document findings

**Medium-term (1-7 days)**:
- [ ] Security audit of all systems
- [ ] Update firewall rules
- [ ] Patch vulnerabilities
- [ ] Review incident with team

---

## 10. Security Monitoring Script

Automated daily security checks:

```python
# backend/scripts/security_check.py
#!/usr/bin/env python3

import subprocess
import json
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
import smtplib
from email.mime.text import MIMEText

def check_vulnerabilities():
    """Check for dependency vulnerabilities."""
    print("Checking for vulnerabilities...")
    result = subprocess.run(
        ["pip-audit", "--format", "json"],
        capture_output=True,
        text=True
    )
    return json.loads(result.stdout)

def check_audit_logs(db_url):
    """Check for suspicious activity in audit logs."""
    engine = create_engine(db_url)
    with engine.connect() as conn:
        # Check for brute force attempts
        result = conn.execute(text("""
            SELECT client_ip, COUNT(*) as failed_count
            FROM audit_logs
            WHERE operation = 'login' AND status = 'failure'
            AND created_at > datetime('now', '-24 hours')
            GROUP BY client_ip
            HAVING failed_count > 3
        """))
        return result.fetchall()

def send_alert(subject, body):
    """Send email alert."""
    msg = MIMEText(body)
    msg["Subject"] = f"[SECURITY] {subject}"
    msg["From"] = "security@yourdomain.com"
    msg["To"] = "admin@yourdomain.com"

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])
        server.send_message(msg)

if __name__ == "__main__":
    # Check vulnerabilities
    vulns = check_vulnerabilities()
    if vulns.get("vulnerabilities"):
        send_alert(
            "Dependency Vulnerabilities Found",
            json.dumps(vulns, indent=2)
        )

    # Check audit logs
    suspicious = check_audit_logs(os.environ["DATABASE_URL"])
    if suspicious:
        send_alert(
            "Suspicious Login Attempts Detected",
            f"IPs with >3 failed logins:\n" +
            "\n".join(f"{ip}: {count}" for ip, count in suspicious)
        )
```

Run daily via cron:
```bash
0 2 * * * python /app/backend/scripts/security_check.py
```

---

## References

- [OWASP Dependency-Check](https://owasp.org/www-project-dependency-check/)
- [pip-audit](https://github.com/pypa/pip-audit)
- [npm audit](https://docs.npmjs.com/cli/audit)
- [Trivy](https://aquasecurity.github.io/trivy/)
- [OWASP Top 10 (2023)](https://owasp.org/Top10/)
- [Bandit](https://bandit.readthedocs.io/)

---

**Last Updated**: June 2024
**Version**: 1.0.0
