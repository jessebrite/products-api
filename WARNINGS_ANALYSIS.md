# Test Warnings Analysis & Fixes

## 📊 Warning Summary

The 171 warnings come from **4 main sources**:

1. **Pydantic V2 Migration Issues** (3 types)
2. **SQLAlchemy 2.0 Issues** (1 type)
3. **Python 3.12 Deprecations** (1 type)
4. **Third-party Library Issues** (1 type)

---

## 🔍 Detailed Breakdown

### 1️⃣ Pydantic Deprecated `Config` Class (90+ warnings)

**Location**: `src/config/settings.py`, `src/schemas/__init__.py` (2 places)

**Issue**: 
```python
# ❌ OLD (Deprecated in Pydantic V2)
class UserResponse(BaseModel):
    class Config:
        from_attributes = True

# ✅ NEW (Pydantic V2 way)
from pydantic import ConfigDict

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
```

**Warning Message**:
```
PydanticDeprecatedSince20: Support for class-based `config` is deprecated, 
use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0.
```

**Why Many Warnings?**: Each test that uses these schemas triggers warnings multiple times (registration, response validation, etc.)

**Fix Status**: ⚠️ **Can be fixed** - Will reduce warnings by ~100

---

### 2️⃣ SQLAlchemy `declarative_base()` (20+ warnings)

**Location**: `src/models/__init__.py:7`

**Issue**:
```python
# ❌ OLD (Deprecated location in SQLAlchemy 2.0)
from sqlalchemy.ext.declarative import declarative_base

# ✅ NEW (SQLAlchemy 2.0 way)
from sqlalchemy.orm import declarative_base
```

**Warning Message**:
```
MovedIn20Warning: The ``declarative_base()`` function is now available as 
sqlalchemy.orm.declarative_base(). (deprecated since: 2.0)
```

**Why Multiple Warnings?**: Triggers once per module import across tests

**Fix Status**: ⚠️ **Can be fixed** - Will reduce warnings by ~20

---

### 3️⃣ Python 3.12 `datetime.utcnow()` (50+ warnings)

**Locations**:
- `src/core/security.py:34` - Our code
- `src/core/security.py:36` - Our code
- `venv/Lib/site-packages/sqlalchemy/sql/schema.py:3592` - SQLAlchemy (external)
- `venv/Lib/site-packages/jose/jwt.py:311` - PyJWT (external)

**Issue**:
```python
# ❌ OLD (Deprecated in Python 3.12)
from datetime import datetime, timedelta
expire = datetime.utcnow() + timedelta(minutes=15)

# ✅ NEW (Python 3.12+)
from datetime import datetime, timedelta, timezone
expire = datetime.now(timezone.utc) + timedelta(minutes=15)
```

**Warning Message**:
```
DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled 
for removal in a future version. Use timezone-aware objects to represent 
datetimes in UTC: datetime.datetime.now(datetime.UTC).
```

**Breakdown**:
- Our code: ~20 warnings ✅ **Can be fixed**
- SQLAlchemy external: ~15 warnings ⚠️ **Wait for update** (not our responsibility)
- PyJWT external: ~15 warnings ⚠️ **Wait for update** (not our responsibility)

**Fix Status**: 
- Our code: ✅ Can fix (~20 warnings)
- External libs: ⚠️ Waiting for library updates (~30 warnings)

---

## 📋 Warning Categories

```
Category                           Count    Source        Fixable
────────────────────────────────────────────────────────────────────
Pydantic Config class              ~90      Our code      ✅ Yes
SQLAlchemy declarative_base()      ~20      Our code      ✅ Yes
datetime.utcnow()                  ~20      Our code      ✅ Yes
datetime.utcnow()                  ~15      SQLAlchemy    ⚠️ No
datetime.utcnow()                  ~15      PyJWT         ⚠️ No
PassLib bcrypt version check       ~10      PassLib       ⚠️ No
Other                              ~1       Various       ⚠️ No
────────────────────────────────────────────────────────────────────
Total                              ~171
Fixable by us                      ~130 (76%)
External dependencies              ~41 (24%)
```

---

## 🛠️ How to Fix

### Fix 1: Update Pydantic Config Classes

**File**: `src/config/settings.py`

```python
# BEFORE
from pydantic import BaseSettings

class Settings(BaseSettings):
    app_name: str = "CRUD API"
    class Config:
        env_file = ".env"
        case_sensitive = False

# AFTER
from pydantic import BaseSettings, ConfigDict

class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False
    )
    app_name: str = "CRUD API"
```

**Impact**: Removes ~40 warnings

---

**File**: `src/schemas/__init__.py`

```python
# BEFORE
class UserResponse(UserBase):
    class Config:
        from_attributes = True

# AFTER
from pydantic import ConfigDict

class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)
```

**Impact**: Removes ~50 warnings

---

### Fix 2: Update SQLAlchemy Import

**File**: `src/models/__init__.py`

```python
# BEFORE
from sqlalchemy.ext.declarative import declarative_base

# AFTER
from sqlalchemy.orm import declarative_base
```

**Impact**: Removes ~20 warnings

---

### Fix 3: Update Python datetime calls

**File**: `src/core/security.py`

```python
# BEFORE
from datetime import datetime, timedelta

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

# AFTER
from datetime import datetime, timedelta, timezone

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
```

**Impact**: Removes ~20 warnings

---

## 📊 Estimated Impact

| Fix | Warnings Removed | Effort | Priority |
|-----|-----------------|--------|----------|
| Pydantic Config | ~90 | 30 min | HIGH |
| SQLAlchemy import | ~20 | 5 min | HIGH |
| datetime.utcnow() | ~20 | 15 min | HIGH |
| **Total Fixable** | **~130** | **50 min** | **HIGH** |
| Remaining (external) | ~41 | N/A | LOW |

---

## ⚠️ Warnings We Can't Fix (External Dependencies)

### SQLAlchemy datetime.utcnow() (~15)
- SQLAlchemy still uses old API
- Waiting for SQLAlchemy 3.0
- Not our code, no action needed

### PyJWT datetime.utcnow() (~15)
- PyJWT (python-jose) still uses old API
- Waiting for library update
- Not our code, no action needed

### PassLib bcrypt version check (~10)
```
WARNING passlib.handlers.bcrypt:bcrypt.py:622 (trapped) error reading 
bcrypt version - this is a known compatibility issue with passlib 1.7.4
```
- PassLib trying to read bcrypt metadata
- Not a real error, just a warning
- Library compatibility issue, not our code

---

## ✅ Action Plan

### Phase 1: Quick Fixes (Recommended - Do Now)
1. ✅ Update Pydantic Config classes (5 minutes)
2. ✅ Update SQLAlchemy imports (2 minutes)
3. ✅ Update datetime calls (5 minutes)
4. **Result**: Reduce warnings from 171 → ~41 (76% reduction!)

### Phase 2: Wait for Library Updates (Future)
- SQLAlchemy 3.0+
- PyJWT updates
- PassLib updates

---

## 📈 Expected Results After Fixes

```
BEFORE FIXES
============
✅ 63 tests passed
⚠️  171 warnings (noise!)
⏱️  ~42 seconds

AFTER FIXES
===========
✅ 63 tests passed (unchanged)
⚠️  ~41 warnings (all from external libs)
⏱️  ~42 seconds (unchanged)

IMPROVEMENT: 76% reduction in warnings!
```

---

## 🎯 Conclusion

**Current Status**: ✅ Tests pass perfectly, warnings are just noise

**Why So Many Warnings?**
1. Deprecated APIs in our code (fixable)
2. Deprecated APIs in external libs (not fixable by us)
3. Each test triggers warnings multiple times due to module imports

**Recommendation**: Apply Phase 1 fixes to clean up ~76% of warnings

**Non-blocking**: External library warnings are expected until those projects update their code

---

## 📝 Implementation Priority

1. **Highest Priority**: Pydantic Config (impacts multiple files, most warnings)
2. **High Priority**: SQLAlchemy import (quick fix, clear solution)
3. **Medium Priority**: datetime.utcnow() (our code, but more complex)
4. **Low Priority**: External library warnings (wait for updates)

Would you like me to implement these fixes to reduce warnings to ~41?
