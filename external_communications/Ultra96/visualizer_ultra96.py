# class implementation for visualizer client
# message queues in this class should be in sync with game engine

import asyncio
import paho.mqtt.client as mqtt
import logging

# constants
CLIENT_USERNAME = "cg4002group7"
CLIENT_PASSWORD = "cg4002GROUP7"
CLIENT_ENDPOINT = "0260bff14c5946a382392749f5535432.s1.eu.hivemq.cloud"
CLIENT_TLS_PORT = 8883

PUBLISH_TOPIC = "test"
SUBSCRIBE_TOPIC = "test2"

class VisualizerClient:
    def __init__(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_subscribe = self.on_subscribe

        self.send_queue = asyncio.Queue()
        self.receive_queue = asyncio.Queue()
        self.loop = asyncio.get_event_loop()

        self.is_running = True
    
    # callback for when client receives a CONNACK response from the server
    def on_connect(self, client, userdata, flags, rc):
        print("Visualizer Client: CONNACK received with code %s." %rc)
        logging.info("Visualizer Client: CONNACK received with code %s." %rc)

        # subscribing in on_connect() means if connection is lost and
        # reconnects, subscriptions will be renewed automatically
        self.client.subscribe(SUBSCRIBE_TOPIC)

    # callback when a publish message is received from the server
    def on_message(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode("utf8")
        logging.info(f"[VisualizerClient on_message]: {(topic, payload)}")
        asyncio.run_coroutine_threadsafe(self.async_put(topic, payload), self.loop)

    # see which topic was subscribed to
    def on_subscribe(self, client, userdata, mid, granted_qos):
        print("Subscribed topic: " + SUBSCRIBE_TOPIC)
        logging.info("Subscribed topic: " + SUBSCRIBE_TOPIC)
    
    # periodically publish messages
    async def publish_messages(self):
        while self.is_running:
            message = await self.send_queue.get()
            self.client.publish(PUBLISH_TOPIC, message)

    async def async_put(self, topic, payload):
        await self.receive_queue.put(payload)
        
    async def start(self):
        self.client.username_pw_set(CLIENT_USERNAME, CLIENT_PASSWORD)
        self.client.tls_set()
        self.client.connect(CLIENT_ENDPOINT, CLIENT_TLS_PORT)
        self.client.loop_start()

        asyncio.create_task(self.publish_messages())
    
    async def stop(self):
        self.is_running = False
        self.client.disconnect()
        print("Visualizer Client disconnected.")
    
# def main():
#     visuazlier_client = VisualizerClient()
#     visuazlier_client.start()
#     try:
#         while True:
#             pass
#     except KeyboardInterrupt:
#         pass
#     visuazlier_client.disconnect()
#     print("Visuazlier on Ultra96 closed.")

# if __name__ == '__main__':
#     main()
