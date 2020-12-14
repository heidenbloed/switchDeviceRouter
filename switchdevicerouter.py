#! venv/bin/python

import logging
import sys
import time
from typing import Union

import paho.mqtt.client as mqtt
import yaml


class SwitchDeviceRouter:

    def __init__(self, switch_device_config: Union[str, dict], mqtt_config: Union[str, dict], debounce_period: float = 0.5):
        switch_device_config = self.__load_yaml(yaml_path=switch_device_config)
        self.__switch_config = switch_device_config["switches"]
        self.__device_config = switch_device_config["devices"]
        self.__mqtt_config = self.__load_yaml(yaml_path=mqtt_config)
        self.__debounce_period = debounce_period
        self.__device_state = {}
        self.__switch_trigger_times = {}
        # Setup MQTT.
        self.__client = mqtt.Client()
        self.__client.on_connect = self.__on_mqtt_connect
        self.__client.on_message = self.__on_mqtt_message
        self.__client.username_pw_set(username=self.__mqtt_config["mqtt_user"], password=self.__mqtt_config["mqtt_password"])
        self.__client.connect(host=self.__mqtt_config["mqtt_host"], port=self.__mqtt_config["mqtt_port"])

    def start_mqtt_loop(self):
        print("Start loop.")
        self.__client.loop_forever()

    def __on_mqtt_connect(self, client: mqtt.Client, _a, _b, return_code: int):
        logging.info(f"Connected to MQTT broker with result code {return_code}.")
        client.subscribe(self.__mqtt_config["switch_topic"])

    def __on_mqtt_message(self, _a, _b, msg: mqtt.MQTTMessage):
        switch_id = msg.payload.decode("utf-8")
        logging.info(f'The switch with the id "{switch_id}" was pressed.')
        if switch_id in self.__switch_config:
            now = time.time()
            if not switch_id in self.__switch_trigger_times or now - self.__switch_trigger_times[switch_id] > self.__debounce_period:
                self.__switch_trigger_times[switch_id] = now
                actions = self.__switch_config[switch_id]
                for action in actions:
                    command, device_name = tuple(action.split(" "))
                    command = self.__replace_toggle(device_name=device_name, action=command)
                    self.__perform_action(device_name=device_name, action=command)
            else:
                logging.warning(f'Signal of switch "{switch_id}" was ignored due to debouncing.')
        else:
            logging.warning(f'Switch "{switch_id}" is unknown.')

    def __replace_toggle(self, device_name: str, action: str):
        if action == "toggle" and action not in self.__device_config[device_name]["available_actions"]:
            if not device_name in self.__device_state:
                self.__device_state[device_name] = True
            self.__device_state[device_name] = not self.__device_state[device_name]
            if self.__device_state[device_name]:
                new_action = "turnoff"
            else:
                new_action = "turnon"
            logging.debug(f'Replace action "{action}" by "{new_action}".')
            return new_action
        else:
            return action

    def __perform_action(self, device_name: str, action: str):
        logging.info(f'Perform action "{action}" for device "{device_name}".')
        if self.__device_config[device_name]["type"] == "yeelight":
            topic = f'{self.__mqtt_config["yeelight_topic"]}/{device_name}'
            logging.debug(f'Publish action "{action}" in topic "{topic}"')
            self.__client.publish(topic, payload=action, qos=2)
        elif self.__device_config[device_name]["type"] == "tuya":
            device_topic = self.__device_config[device_name]["topic"] if "topic" in self.__device_config[device_name] else device_name
            topic = f"{self.__mqtt_config['tuya_topic']}/{device_topic}/command"
            tuya_action = {
                "turnon": "true",
                "turnoff": "false"
            }[action]
            logging.debug(f'Publish action "{tuya_action}" in topic "{topic}"')
            self.__client.publish(topic, payload=tuya_action, qos=2)

    @staticmethod
    def __load_yaml(yaml_path: Union[str, dict]):
        if isinstance(yaml_path, dict):
            # Config already loaded
            return yaml_path
        else:
            with open(yaml_path, 'r') as yp:
                return yaml.safe_load(yp)


if __name__ == "__main__":
    # Setup logging.
    logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=logging.DEBUG, datefmt='%Y-%m-%d %H:%M:%S',
                        stream=sys.stdout)
    # Setup switch device router.
    sdr = SwitchDeviceRouter(switch_device_config="switch_device_config.yaml", mqtt_config="mqtt_config.yaml")
    sdr.start_mqtt_loop()
