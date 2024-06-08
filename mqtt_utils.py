import os
import adafruit_minimqtt.adafruit_minimqtt as MQTT
import adafruit_connection_manager
import glucose_value_holder
import json

def create_mqtt_client(esp32_radio):
    mqtt_host = os.getenv("MQTT_HOST")
    mqtt_username = os.getenv("MQTT_USERNAME")
    mqtt_password = os.getenv("MQTT_PASSWORD")

    pool = adafruit_connection_manager.get_radio_socketpool(esp32_radio)
    ssl_context = adafruit_connection_manager.get_radio_ssl_context(esp32_radio)

    mqtt_client = MQTT.MQTT(
        broker=mqtt_host,
        username=mqtt_username,
        password=mqtt_password,
        port=1883,
        client_id="pyportal-pynt",
        socket_pool=pool,
        ssl_context=ssl_context
    )

    mqtt_client.on_connect = connect
    mqtt_client.on_disconnect = disconnect
    mqtt_client.on_subscribe = subscribe
    mqtt_client.on_unsubscribe = unsubscribe
    mqtt_client.on_publish = publish
    mqtt_client.on_message = message

    return mqtt_client

def connect(mqtt_client, userdata, flags, rc):
    # This function will be called when the mqtt_client is connected
    # successfully to the broker.
    print("Connected to MQTT")
    print("Flags: {0}\n RC: {1}".format(flags, rc))



def disconnect(mqtt_client, userdata, rc):
    # This method is called when the mqtt_client disconnects
    # from the broker.
    print("Disconnected from MQTT Broker!")


def subscribe(mqtt_client, userdata, topic, granted_qos):
    # This method is called when the mqtt_client subscribes to a new feed.
    print("Subscribed to {0} with QOS level {1}".format(topic, granted_qos))


def unsubscribe(mqtt_client, userdata, topic, pid):
    # This method is called when the mqtt_client unsubscribes from a feed.
    print("Unsubscribed from {0} with PID {1}".format(topic, pid))


def publish(mqtt_client, userdata, topic, pid):
    # This method is called when the mqtt_client publishes data to a feed.
    print("Published to {0} with PID {1}".format(topic, pid))


def message(client, topic, message):
    print("New message on topic {0}: {1}".format(topic, message))
    json_message = json.loads(message)

    mgdl_value = json_message.get("mgdl", None)
    mmol_value = json_message.get("mmol", None)
    trend_value = json_message.get("trend", "NotComputable")
    datetime_value = json_message.get("datetime", 0)
    time_value = json_message.get("time", "")
    invalid_value = json_message.get("invalid", True)

    # Handle None values appropriately (e.g., set to a default value or handle as needed)
    mgdl_value = int(mgdl_value) if mgdl_value is not None else None
    mmol_value = float(mmol_value) if mmol_value is not None else None

    glucose_value_holder.glucose_value.update_values(mgdl_value, mmol_value, trend_value, datetime_value, time_value, invalid_value)
