import time
import logging
import RPi.GPIO as GPIO
from lib.eventhook import EventHook

logger = logging.getLogger(__name__)


SHORT_WAIT = .2 #S (200ms)
"""
    The purpose of this class is to map the idea of a garage door to the pinouts on 
    the raspberrypi. It provides methods to control the garage door and also provides
    and event hook to notify you of the state change. It also doesn't maintain any
    state internally but rather relies directly on reading the pin.
"""
class GarageDoor(object):
    
    def __init__(self, config):

        # Config
        self.relay_stop_pin = config['relay_stop']
        self.relay_open_pin = config['relay_open']
        self.relay_close_pin = config['relay_close']
        self.relay_step_pin = config['relay_step']
        self.state_pin = config['state']
        self.button_pin = config['button']
        self.id = config['id']
        self.mode = int(config.get('state_mode') == 'normally_closed')
        self.invert_relay = bool(config.get('invert_relay'))

        # State
        self._state = None
        self.onStateChange = EventHook()
        

        # Button
        self.onButtonPress = EventHook()

        # Set relay pin to output, state pin to input, and add a change listener to the state pin
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.relay_stop_pin, GPIO.OUT)
        GPIO.setup(self.relay_open_pin, GPIO.OUT)
        GPIO.setup(self.relay_close_pin, GPIO.OUT)
        GPIO.setup(self.relay_step_pin, GPIO.OUT)

        GPIO.setup(self.state_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(self.state_pin, GPIO.BOTH, callback=self.__stateChanged, bouncetime=300)

        GPIO.setup(self.button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(self.button_pin, GPIO.BOTH, callback=self.__buttonChanged, bouncetime=100)


        # Set default relay state to false (off)
        GPIO.output(self.relay_stop_pin, self.invert_relay)
        GPIO.output(self.relay_open_pin, self.invert_relay)
        GPIO.output(self.relay_close_pin, self.invert_relay)
        GPIO.output(self.relay_step_pin, self.invert_relay)

    # Release rpi resources
    def __del__(self):
        GPIO.cleanup()

    # These methods all just mimick the button press, they dont differ other than that
    # but for api sake I'll create three methods. Also later we may want to react to state
    # changes or do things differently depending on the intended action

    def stop(self):
        self.__press_stop()

    def open(self):
        if self.state == 'closed':
            self.__press_step()

    def close(self):
        if self.state == 'open':
            self.__press_step()

    def step(self):
        if self.state == 'closed':
            self.__press_step()

    # State is a read only property that actually gets its value from the pin
    @property
    def state(self):
        # Read the mode from the config. Then compare the mode to the current state. IE. If the circuit is normally closed and the state is 1 then the circuit is closed.
        # and vice versa for normally open
        try:
            state = GPIO.input(self.state_pin)
            logger.debug(f'State value: {state} for door {self.id}')
            if state == 0:
                return 'closed'
            else:
                return 'open'
        except Exception as e:
            logger.error(f"Error reading state pin {self.state_pin}: {e}")
            return 'unknown'

    # Button is a read only property that actually gets its value from the pin
    @property
    def button(self):
        # Read the mode from the config. Then compare the mode to the current state. IE. If the circuit is normally closed and the state is 1 then the circuit is closed.
        # and vice versa for normally open
        button = GPIO.input(self.button_pin)
        return button

    # Mimick a button press by switching the GPIO pin on and off quickly
    def __press_stop(self):
        GPIO.output(self.relay_stop_pin, not self.invert_relay)
        time.sleep(SHORT_WAIT)
        GPIO.output(self.relay_stop_pin, self.invert_relay)

    def __press_open(self):
        GPIO.output(self.relay_open_pin, not self.invert_relay)
        time.sleep(SHORT_WAIT)
        GPIO.output(self.relay_open_pin, self.invert_relay)

    def __press_close(self):
        GPIO.output(self.relay_close_pin, not self.invert_relay)
        time.sleep(SHORT_WAIT)
        GPIO.output(self.relay_close_pin, self.invert_relay)

    def __press_step(self):
        GPIO.output(self.relay_step_pin, not self.invert_relay)
        time.sleep(SHORT_WAIT)
        GPIO.output(self.relay_step_pin, self.invert_relay)

   
    # Provide an event for when the state pin changes
    def __stateChanged(self, channel):
        if channel == self.state_pin:
            # Had some issues getting an accurate value so we are going to wait for a short timeout
            # after a statechange and then grab the state
            time.sleep(SHORT_WAIT)
            self.onStateChange.fire(self.state)


    def __buttonChanged(self, channel):
        if channel == self.button_pin:  
            self.onButtonPress.fire()
                    
