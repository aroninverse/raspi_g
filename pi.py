import RPi.GPIO as GPIO
import time
import paho.mqtt.client as mqtt
import minimalmodbus
import json

SUB_TOPIC = "pi_g/device/0001/cmd"
PUB_TOPIC = "pi_g/device/0001/data"

gpio_list = [26, 19, 13, 6, 5]


def mqtt_on_connect(client, userdata, flags, rc):
    print(f"[MQTT] Connected with result code (rc = {rc})")
    mqtt_client.subscribe(SUB_TOPIC)


def mqtt_on_message(client, userdata, msg):
    payload = msg.payload.decode('ascii')
    print(f"[MQTT] {msg.topic} => {payload}")

    try:
        jobj = json.loads(payload)
        pin = jobj["pin"]
        value = jobj["value"]
        gpio = gpio_list[pin - 1]
        print(f"Set gpio-{gpio} to {value}")
        GPIO.output(gpio, False if value == 1 else True)
    except:
        pass


if __name__ == '__main__':
    print("Rasp PI Gateway.")

    # Init GPIO
    GPIO.setmode(GPIO.BCM)
    for gpio in gpio_list:
        GPIO.setup(gpio, GPIO.OUT)
        GPIO.output(gpio, False)

    # Init modbus
    modbus = minimalmodbus.Instrument('/dev/ttyAMA0', 18)
    modbus.serial.baudrate = 9600
    modbus.serial.timeout = 1

    # Init MQTT
    mqtt_client = mqtt.Client(client_id="rasp0001", clean_session=False)
    mqtt_client.on_connect = mqtt_on_connect
    mqtt_client.on_message = mqtt_on_message
    mqtt_client.connect("broker.emqx.io", 1883, 60)
    mqtt_client.loop_start()

    while True:
        try:
            data = {}
            data['temp'] = modbus.read_register(0, 1)
            data['humi'] = modbus.read_register(1, 1)
            print(f"Temp: {data['temp']}, Humi: {data['humi']}")
            mqtt_client.publish(PUB_TOPIC, json.dumps(data), 0, False)
        except:
            pass
        time.sleep(1)
