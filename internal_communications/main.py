# COMMAND: sudo -E env "PATH=$PATH" /home/yitching/capstone/testingEnv/bin/python /home/yitching/capstone/CG4002_capstone/internal_communications/main.py
import logging
import threading
import asyncio
import queue
import concurrent.futures
from laptop_relay_node import LaptopClient
from device import BeetleDevice

# Set up logging configuration
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s', 
                    filename='app.log',
                    filemode='w')

service_uuid = "0000dfb0-0000-1000-8000-00805f9b34fb"
characteristic_uuid = "0000dfb1-0000-1000-8000-00805f9b34fb"  # Replace with the UUID of your characteristic
beetle_devices = [
    {"address": "D0:39:72:E4:86:9C", "service_uuid": service_uuid, "characteristic_uuid": characteristic_uuid, "name": "b1"}, # Glove Beetle 2
    {"address": "D0:39:72:E4:8C:09", "service_uuid": service_uuid, "characteristic_uuid": characteristic_uuid, "name": "b2"},
    {"address": "D0:39:72:E4:86:F8", "service_uuid": service_uuid, "characteristic_uuid": characteristic_uuid, "name": "b3"}, # Vest Beetle 1
    {"address": "D0:39:72:E4:8C:4D", "service_uuid": service_uuid, "characteristic_uuid": characteristic_uuid, "name": "b4"}, # Gun Beetle 1
    {"address": "C4:BE:84:20:19:73", "service_uuid": service_uuid, "characteristic_uuid": characteristic_uuid, "name": "b5"}, # Glove Beetle 1
    {"address": "D0:39:72:E4:80:9F", "service_uuid": service_uuid, "characteristic_uuid": characteristic_uuid, "name": "b6"}, # Gun Beetle 2
]

HOSTNAME = "172.25.110.74"
REMOTE_BIND_PORT = 8080

class BeetleMain(threading.Thread):
    def __init__(self):
        super().__init__()
        self.send_queue = queue.Queue()
        self.receive_queue = queue.Queue()
        self.relay_node = LaptopClient(HOSTNAME, REMOTE_BIND_PORT)
        self.beetle_threads = []


    # instantiate Beetles, Relay Node, and the pipeline
    def run(self):
        self.spawn_beetle_threads()
        self.relay_node.start()

        # Wait for the event to signal that the loop is ready
        self.relay_node.loop_ready.wait()

        # run LaptopClient's async start method
        # loop = asyncio.get_event_loop()
        loop = self.relay_node.loop
        # loop.run_until_complete(self.relay_node.async_start())
        asyncio.run_coroutine_threadsafe(self.relay_node.async_start(), loop)

        outgoingThread = threading.Thread(target=self.redirect_Beetle_To_RelayNode())
        incomingThread = threading.Thread(target=self.redirect_RelayNode_To_Beetle())
        outgoingThread.start()
        print("Starting redirect_Beetle_To_RelayNode...")
        incomingThread.start()
        print("Starting redirect_RelayNode_To_Beetle...")    
    
    def redirect_Beetle_To_RelayNode(self):
        while True:
            data = self.send_queue.get()
            print(f"Data taken: {data} | Queue Size After Taking: {self.send_queue.qsize()}")
            asyncio.run_coroutine_threadsafe(self.relay_node.enqueue_data(data), self.relay_node.loop)
            print(f"Data transferred: {data}")

    def redirect_RelayNode_To_Beetle(self):
        while True:
            loop = self.relay_node.loop
            future = asyncio.run_coroutine_threadsafe(self.relay_node.dequeue_data(), loop)
            data = future.result()

            # send data to beetle
            self.receive_queue.put(data)
            print(f"Data transferred: {data}")

    def spawn_beetle_threads(self):
        for device_info in beetle_devices:
            beetle = BeetleDevice(device_info["address"], device_info["service_uuid"], device_info["characteristic_uuid"], device_info["name"], self.send_queue, self.receive_queue)
            thread = threading.Thread(target=beetle.beetle_handler)
            self.beetle_threads.append(thread)
            thread.start()
        
def main():
    beetle = BeetleMain()
    beetle.start()
    beetle.join()

if __name__ == '__main__':
    main()
