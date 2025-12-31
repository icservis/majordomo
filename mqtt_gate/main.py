import os
import binascii
import json
import logging
import yaml
import paho.mqtt.client as mqtt
import re

from lib.garage import GarageDoor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info("Welcome to GarageBerryPi!")

# Update the mqtt state topic
def update_state(value, topic):
    logger.info(f"State change triggered: {topic} -> {value}")
    client.publish(topic, value, retain=True)

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info(f"Connected with result code: {mqtt.connack_string(rc)}")
        logger.info(f"Listening for server status on {server_status_topic}")
        client.subscribe(server_status_topic)
        for config in CONFIG['doors']:
            availability_topic = config['availability_topic']
            client.publish(availability_topic, "online", retain=False)
            command_topic = config['command_topic']
            logger.info(f"Listening for commands on {command_topic}")
            client.subscribe(command_topic)
    else:
        logger.error(f"Failed to connect with result code: {mqtt.connack_string(rc)}")

# Callback for disconnection
def on_disconnect(client, userdata, rc):
    if rc != 0:
        logger.warning(f"Unexpected disconnection (rc={rc}). Attempting to reconnect...")
    else:
        logger.info("Disconnected gracefully")

# Validate MQTT command message
def validate_command(message):
    """Validate and sanitize MQTT command message."""
    if not message or not isinstance(message, str):
        return None
    allowed_commands = ['STEP', 'OPEN', 'CLOSE', 'STOP']
    message = message.strip().upper()
    return message if message in allowed_commands else None

# Execute the specified command for a door
def execute_command(door, command):
    try:
        doorName = door.name
    except (AttributeError, KeyError):
        doorName = getattr(door, 'id', 'unknown')
    
    current_state = door.state
    logger.info(f"Executing command {command} for door {doorName} (current state: {current_state})")
    
    # Execute command based on current state and command type
    if command == "STOP":
        door.stop()
        logger.info(f"STOP command executed for door {doorName}")
    elif command == "STEP":
        if current_state == 'closed':
            door.step()
            logger.info(f"STEP command executed for door {doorName}")
        else:
            logger.warning(f"STEP command ignored - door {doorName} is {current_state}, must be closed")
    elif command == "OPEN":
        if current_state == 'closed':
            door.open()
            logger.info(f"OPEN command executed for door {doorName}")
        else:
            logger.warning(f"OPEN command ignored - door {doorName} is {current_state}, must be closed")
    elif command == "CLOSE":
        if current_state == 'open':
            door.close()
            logger.info(f"CLOSE command executed for door {doorName}")
        else:
            logger.warning(f"CLOSE command ignored - door {doorName} is {current_state}, must be open")
    else:
        logger.warning(f"Unknown command: {command}")

# Load and validate configuration
def load_config():
    """Load and validate configuration file."""
    config_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'config.yaml')
    try:
        with open(config_path, 'r') as ymlfile:
            config = yaml.safe_load(ymlfile)
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_path}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML configuration: {e}")
        raise
    
    # Validate required keys
    required_keys = ['mqtt', 'doors']
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required config key: {key}")
    
    # Validate mqtt section
    mqtt_required = ['host', 'port', 'user', 'password', 'server_status_topic']
    for key in mqtt_required:
        if key not in config['mqtt']:
            raise ValueError(f"Missing required mqtt config key: {key}")
    
    if not config.get('doors') or not isinstance(config['doors'], list):
        raise ValueError("Config must contain a non-empty 'doors' list")
    
    return config

CONFIG = load_config()

### SETUP MQTT ###
server_status_topic = CONFIG['mqtt']['server_status_topic']
user = CONFIG['mqtt']['user']
password = CONFIG['mqtt']['password']
host = CONFIG['mqtt']['host']
port = int(CONFIG['mqtt']['port'])
discovery = bool(CONFIG['mqtt'].get('discovery'))
if 'discovery_prefix' not in CONFIG['mqtt']:
    discovery_prefix = 'homeassistant'
else:
    discovery_prefix = CONFIG['mqtt']['discovery_prefix']

# Use paho-mqtt 2.x API - callback_api_version parameter
client = mqtt.Client(
    client_id="MQTTGarageDoor_" + binascii.hexlify(os.urandom(32)).decode(),
    callback_api_version=mqtt.CallbackAPIVersion.VERSION1
)

client.on_connect = on_connect
client.on_disconnect = on_disconnect

client.username_pw_set(user, password=password)
try:
    client.connect(host, port, 60)
except Exception as e:
    logger.error(f"Failed to connect to MQTT broker at {host}:{port}: {e}")
    raise
### SETUP END ###

### MAIN LOOP ###
if __name__ == "__main__":
    # Create door objects and create callback functions
    for doorCfg in CONFIG['doors']:

        # If no name it set, then set to id
        if not doorCfg['name']:
            doorCfg['name'] = doorCfg['id']

        # Sanitize id value for mqtt (remove non-word characters, replace spaces with underscores)
        doorCfg['id'] = re.sub(r'\W+', '', re.sub(r'\s', '_', doorCfg['id']))

        if discovery is True:
            base_topic = discovery_prefix + "/cover/" + doorCfg['id']
            config_topic = base_topic + "/config"
            doorCfg['command_topic'] = base_topic + "/set"
            doorCfg['state_topic'] = base_topic + "/state"
        
        command_topic = doorCfg['command_topic']
        state_topic = doorCfg['state_topic']


        door = GarageDoor(doorCfg)

        # Callback per door that passes a reference to the door
        def on_message(client, userdata, msg, door=door):
            try:
                message = str(msg.payload.decode("utf-8"))
                logger.info(f"Receiving message: {message}")
                validated_command = validate_command(message)
                if validated_command:
                    execute_command(door, validated_command)
                else:
                    logger.warning(f"Invalid command received: {message}")
            except Exception as e:
                logger.error(f"Error processing message: {e}")

        # Callback per door that passes the doors state topic
        def on_state_change(value, topic=state_topic):
            update_state(value, topic)

        client.message_callback_add(command_topic, on_message)

        # Callback on status from server
        def on_server_status_message(client, userdata, msg, door=door):
            try:
                message = str(msg.payload.decode("utf-8"))
                logger.info(f"Receiving status: {message}")
                for config in CONFIG['doors']:
                    availability_topic = config['availability_topic']
                    client.publish(availability_topic, "online", retain=False)
                client.publish(state_topic, door.state, retain=True)
            except Exception as e:
                logger.error(f"Error processing server status message: {e}")

        client.message_callback_add(server_status_topic, on_server_status_message)

        # You can add additional listeners here and they will all be executed when the door state changes
        door.onStateChange.addHandler(on_state_change)

        def on_buttonPress():
            logger.info("Button pressed")
        door.onButtonPress.addHandler(on_buttonPress)
        

        # Publish initial door state
        client.publish(state_topic, door.state, retain=True)

        # If discovery is enabled publish configuration
        if discovery is True:
            config_json = json.dumps({
                "name": doorCfg['name'],
                "command_topic": command_topic,
                "state_topic": state_topic
            })
            client.publish(config_topic, config_json, retain=True)

    # Main loop
    client.loop_forever()


