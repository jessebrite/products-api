# Secrets Management & Vault System

## Overview

This project uses a centralized **Secrets Vault** system to securely manage all sensitive configuration like API keys, database credentials, and encryption secrets. No secrets are hardcoded in the source code.

## Architecture

```
Application Code
      ↓
Vault (src/vault.py)
      ↓
Environment Variables
      ↓
.env file (gitignored)
```

## Key Files

| File | Purpose |
|------|---------|
| `src/vault.py` | Centralized secret management system |
| `.env` | Development secrets (gitignored) |
| `.env.example` | Template showing all available secrets |
| `src/config/settings.py` | Settings that use vault for secrets |

## How It Works

### 1. Environment Setup

All secrets are stored as environment variables. These typically come from a `.env` file:

```bash
# .env file (not in version control)
SECRET_KEY=my-super-secret-key-32-chars-minimum
DATABASE_URL=postgresql://user:password@localhost/dbname
API_KEY=your-api-key-here
```

### 2. Accessing Secrets

Code never directly accesses environment variables or hardcodes secrets. Instead, it uses the vault:

```python
from src.vault import vault

# Get a required secret (will raise error if missing)
secret_key = vault.get_secret("SECRET_KEY")

# Get an optional secret (returns None if missing)
api_key = vault.get_optional_secret("API_KEY")

# Check if a secret exists
if vault.has_secret("STRIPE_KEY"):
    stripe_key = vault.get_secret("STRIPE_KEY")
```

### 3. Configuration

Settings are automatically loaded from vault:

```python
from src.config import settings

# These are loaded from vault/environment
secret_key = settings.secret_key  # From vault
database_url = settings.database_url  # From vault
```

## Setup Instructions

### Development Setup

1. **Copy the template:**
   ```bash
   cp .env.example .env
   ```

2. **Add your development secrets:**
   ```bash
   # .env file
   SECRET_KEY=your-development-secret-key-here
   DATABASE_URL=sqlite:///./app.db
   ```

3. **Verify secrets are loaded:**
   ```bash
   python -c "from src.config import settings; print(f'Loaded: {settings.app_name}')"
   ```

### Production Setup

For production, set environment variables through your deployment platform:

- **Docker:** Environment variables in `.env` or `docker-compose.yml`
- **Kubernetes:** Secrets in deployment manifest
- **Heroku:** Config vars in dashboard
- **AWS:** Systems Manager Parameter Store or Secrets Manager
- **Azure:** Key Vault
- **Docker Compose:**
  ```yaml
  services:
    app:
      environment:
        - SECRET_KEY=${SECRET_KEY}
        - DATABASE_URL=${DATABASE_URL}
  ```

## Vault API Reference

### Getting Secrets

```python
from src.vault import vault

# Required secret (raises error if missing)
secret = vault.get_secret("SECRET_KEY")

# Optional secret (returns None if missing)
optional = vault.get_optional_secret("OPTIONAL_KEY", default="default_value")

# Check if exists
exists = vault.has_secret("SOME_KEY")

# Get all accessed secrets (values masked)
accessed = vault.get_all_secrets(include_values=False)
```

### Validation

```python
# Validate all required secrets are present
try:
    vault.validate_secrets()
    print("All secrets OK!")
except ValueError as e:
    print(f"Missing secrets: {e}")
```

### Safe Logging

```python
# Obfuscate secrets for safe logging/display
obfuscated = vault.obfuscate_secret("my-secret-key-12345")
# Output: "my-s****5"
print(f"Using secret: {obfuscated}")
```

## Required Secrets

These secrets MUST be set before the application starts:

| Secret | Purpose | Example |
|--------|---------|---------|
| `SECRET_KEY` | JWT encryption key | Generate with: `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `DATABASE_URL` | Database connection | `sqlite:///./app.db` or `postgresql://user:pass@host/db` |

## Optional Secrets

These are optional and used only if your application needs them:

| Secret | Purpose |
|--------|---------|
| `SMTP_SERVER` | Email server |
| `SMTP_USERNAME` | Email username |
| `SMTP_PASSWORD` | Email password |
| `SENDGRID_API_KEY` | SendGrid API key |
| `STRIPE_API_KEY` | Stripe API key |
| `AWS_ACCESS_KEY_ID` | AWS credentials |
| `AWS_SECRET_ACCESS_KEY` | AWS credentials |

## Security Best Practices

### ✅ DO

- ✅ Store `.env` in `.gitignore` (it's already there)
- ✅ Use strong, random keys (32+ characters)
- ✅ Rotate secrets regularly
- ✅ Use different secrets for each environment
- ✅ Use vault for ALL sensitive data
- ✅ Use secrets management services in production (AWS Secrets Manager, Azure Key Vault, etc.)
- ✅ Audit who has access to secrets
- ✅ Use environment-specific secrets

### ❌ DON'T

- ❌ Commit `.env` to version control
- ❌ Hardcode secrets in code
- ❌ Share `.env` files via email or chat
- ❌ Use default/example secrets in production
- ❌ Log or print raw secrets
- ❌ Use the same secrets across environments
- ❌ Store secrets in code comments
- ❌ Enable debug mode in production

## Generating Secure Keys

Generate a secure `SECRET_KEY`:

```bash
# Option 1: Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Option 2: OpenSSL
openssl rand -base64 32

# Option 3: On Windows (PowerShell)
[Convert]::ToBase64String((Get-Random -InputObject (0..255) -Count 32))
```

## Troubleshooting

### Error: "Required secret 'SECRET_KEY' not found"

**Solution:** Set the secret in your `.env` file:
```bash
echo "SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')" >> .env
```

### Error: "No module named 'src.vault'"

**Solution:** Make sure you're running from the project root and src/vault.py exists

### Secrets not loading

**Solution:** Check that:
1. `.env` file exists in project root
2. Secrets are in correct format: `KEY=value`
3. No spaces around `=`: ✅ `KEY=value` vs ❌ `KEY = value`

## Testing with Secrets

Tests automatically use development secrets from `.env`:

```bash
pytest tests/ -v
```

To use specific secrets for tests, create `.env.test`:
```bash
# .env.test
SECRET_KEY=test-secret-key-for-testing
DATABASE_URL=sqlite:///./test.db
```

## Integration Examples

### Django

```python
from src.vault import vault

SECRET_KEY = vault.get_secret("SECRET_KEY")
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'URL': vault.get_secret("DATABASE_URL"),
    }
}
```

### FastAPI (Already Implemented)

```python
from src.config import settings

app = FastAPI()
# Settings already loads from vault
print(settings.secret_key)  # Loaded from vault
```

### Flask

```python
from src.vault import vault

app = Flask(__name__)
app.config['SECRET_KEY'] = vault.get_secret("SECRET_KEY")
```

## Migration from Hardcoded Secrets

If you had secrets hardcoded, here's how to migrate:

1. **Identify all hardcoded secrets** in code
2. **Move them to `.env`:**
   ```bash
   # .env
   API_KEY=your-hardcoded-api-key-value
   ```
3. **Update code to use vault:**
   ```python
   # Before
   API_KEY = "your-hardcoded-api-key-value"
   
   # After
   from src.vault import vault
   API_KEY = vault.get_secret("API_KEY")
   ```
4. **Remove hardcoded values** from source code
5. **Commit and push** (`.env` is gitignored)

## Related Files

- 🔐 Secret management: `src/vault.py`
- ⚙️ Settings configuration: `src/config/settings.py`
- 📝 Environment template: `.env.example`
- 🔒 Git ignore rules: `.gitignore`
- 📚 Main README: `README.md`

## More Resources

- [12 Factor App - Config](https://12factor.net/config)
- [OWASP - Secrets Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [Python-dotenv Documentation](https://python-dotenv.readthedocs.io/)
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)

---

**Last Updated:** 2025-11-21  
**Vault Version:** 1.0  
**Security Level:** Production-Ready ✅
