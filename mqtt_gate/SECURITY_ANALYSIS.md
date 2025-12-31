# Security and Code Quality Analysis Report

## Critical Security Issues

### 1. **JSON Injection Vulnerability (main.py:129)**
**Severity:** HIGH
**Location:** Line 129
**Issue:** JSON is constructed via string concatenation, making it vulnerable to injection attacks if door names contain special characters.
```python
client.publish(config_topic,'{"name": "' + doorCfg['name'] + '", ...}')
```
**Fix:** Use `json.dumps()` to properly escape JSON.

### 2. **Outdated Dependencies with Known Vulnerabilities**
**Severity:** HIGH
**Location:** requirements.txt
**Issues:**
- `paho_mqtt==1.2` (from ~2016) - Current version is 1.6.x with security fixes
- `PyYAML==3.12` (from ~2016) - Current version is 6.x with security fixes

### 3. **Bare Exception Handling**
**Severity:** MEDIUM
**Location:** main.py:32
**Issue:** Bare `except:` clause catches all exceptions including system exits.
```python
try:
    doorName = door.name
except:
    doorName = door.id
```
**Fix:** Catch specific exceptions.

### 4. **No Input Validation on MQTT Messages**
**Severity:** MEDIUM
**Location:** main.py:95-97
**Issue:** MQTT messages are not validated before processing commands.
**Fix:** Validate and sanitize incoming messages.

### 5. **No MQTT Connection Error Handling**
**Severity:** MEDIUM
**Location:** main.py:66
**Issue:** No error handling for connection failures, no reconnection logic.
**Fix:** Add connection error handling and automatic reconnection.

## Code Quality Issues

### 6. **Incorrect Regex Pattern**
**Severity:** MEDIUM
**Location:** main.py:79
**Issue:** `'W+'` should be `'\W+'` (non-word characters). Current pattern matches literal 'W' character.
```python
doorCfg['id'] = re.sub('W+', '', re.sub('s', ' ', doorCfg['id']))
```

### 7. **Deprecated Python 2 Code**
**Severity:** LOW
**Location:** lib/eventhook.py:18
**Issue:** Uses `im_self` which is Python 2 style. Should use `__self__` for Python 3.

### 8. **No Logging Framework**
**Severity:** LOW
**Location:** Throughout
**Issue:** Uses `print()` statements instead of proper logging.
**Fix:** Use Python's `logging` module.

### 9. **Global Variables**
**Severity:** LOW
**Location:** main.py
**Issue:** `client`, `CONFIG`, etc. are global variables.
**Fix:** Refactor to use classes or functions with proper scope.

### 10. **GPIO Cleanup Issues**
**Severity:** MEDIUM
**Location:** lib/garage.py:58-59
**Issue:** `__del__` method cleanup can cause issues with multiple instances and is unreliable.
**Fix:** Use context managers or explicit cleanup methods.

### 11. **String Formatting**
**Severity:** LOW
**Location:** Throughout
**Issue:** Uses old `%` formatting instead of f-strings or `.format()`.

### 12. **No Type Hints**
**Severity:** LOW
**Location:** Throughout
**Issue:** Missing type hints for better code maintainability.

### 13. **Missing Configuration Validation**
**Severity:** MEDIUM
**Location:** main.py:46-47
**Issue:** No validation that required config keys exist before use.
**Fix:** Add validation with clear error messages.

### 14. **YAML Loading**
**Severity:** LOW
**Location:** main.py:47
**Issue:** Uses `yaml.load()` with `FullLoader`. While safe, `yaml.safe_load()` is more explicit.
**Fix:** Use `yaml.safe_load()`.

## Proposed Fixes

See `FIXES.md` for detailed implementation of fixes.

