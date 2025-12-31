# Proposed Fixes Implementation Guide

## Priority 1: Critical Security Fixes

### Fix 1: Update Dependencies
Update `requirements.txt`:
```
paho-mqtt>=1.6.1
PyYAML>=6.0.1
```

### Fix 2: JSON Injection Fix
Replace string concatenation with `json.dumps()`:
```python
import json
# Replace line 129:
config_json = json.dumps({
    "name": doorCfg['name'],
    "command_topic": command_topic,
    "state_topic": state_topic
})
client.publish(config_topic, config_json, retain=True)
```

### Fix 3: Input Validation
Add message validation:
```python
def validate_command(message):
    """Validate MQTT command message."""
    allowed_commands = ['STEP', 'OPEN', 'CLOSE', 'STOP']
    message = message.strip().upper()
    return message if message in allowed_commands else None
```

### Fix 4: Exception Handling
Replace bare except:
```python
try:
    doorName = door.name
except (AttributeError, KeyError):
    doorName = door.id
```

### Fix 5: Regex Pattern Fix
```python
# Line 79 - fix regex
doorCfg['id'] = re.sub(r'\W+', '', re.sub(r'\s', '_', doorCfg['id']))
```

## Priority 2: Code Quality Improvements

### Fix 6: Add Logging
Replace print statements with logging:
```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

### Fix 7: MQTT Connection Handling
Add reconnection logic and error handling:
```python
def on_disconnect(client, userdata, rc):
    logger.warning(f"Disconnected with result code {rc}")
    if rc != 0:
        logger.info("Attempting to reconnect...")
        client.reconnect()

client.on_disconnect = on_disconnect
```

### Fix 8: Configuration Validation
Add validation:
```python
def validate_config(config):
    required_keys = ['mqtt', 'doors']
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required config key: {key}")
    # Validate mqtt section
    mqtt_required = ['host', 'port', 'user', 'password', 'server_status_topic']
    for key in mqtt_required:
        if key not in config['mqtt']:
            raise ValueError(f"Missing required mqtt config key: {key}")
```

### Fix 9: EventHook Python 3 Fix
```python
# lib/eventhook.py line 18
if hasattr(theHandler, '__self__') and theHandler.__self__ == inObject:
    self.removeHandler(theHandler)
```

### Fix 10: YAML Safe Load
```python
CONFIG = yaml.safe_load(ymlfile)
```

