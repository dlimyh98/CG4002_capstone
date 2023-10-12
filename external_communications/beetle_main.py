# wrapper class for all Beetles, Relay Node Client and Pipeline (should be a thread)

import threading
import asyncio
import queue
from laptop_relay_node import LaptopClient
from device import BeetleDevice


# constants
service_uuid = "0000dfb0-0000-1000-8000-00805f9b34fb"
characteristic_uuid = "0000dfb1-0000-1000-8000-00805f9b34fb"  # Replace with the UUID of your characteristic
beetle_devices = [
    {"address": "D0:39:72:E4:86:9C", "service_uuid": service_uuid, "characteristic_uuid": characteristic_uuid, "name": "b"},
    {"address": "D0:39:72:E4:8C:09", "service_uuid": service_uuid, "characteristic_uuid": characteristic_uuid, "name": "c"},
    {"address": "D0:39:72:E4:86:F8", "service_uuid": service_uuid, "characteristic_uuid": characteristic_uuid, "name": "d"}, # Vest Beetle 1
    {"address": "D0:39:72:E4:8C:4D", "service_uuid": service_uuid, "characteristic_uuid": characteristic_uuid, "name": "e"}, # Gun Beetle 1
    {"address": "C4:BE:84:20:19:73", "service_uuid": service_uuid, "characteristic_uuid": characteristic_uuid, "name": "f"}, # Glove Beetle 1
    {"address": "D0:39:72:E4:80:9F", "service_uuid": service_uuid, "characteristic_uuid": characteristic_uuid, "name": "g"}, # Gun Beetle 2
]

HOSTNAME = "127.0.0.1"
REMOTE_BIND_PORT = 8080


class BeetleMain(threading.Thread):
    def __init__(self):
        super().__init__()
        self.global_queue = queue.Queue()
        self.relay_node = LaptopClient(HOSTNAME, REMOTE_BIND_PORT)
        self.beetle_threads = []


    # instantiate Beetles, Relay Node, and the pipeline
    def run(self):
        self.spawn_beetle_threads()
        self.relay_node.start()

        # Wait for the event to signal that the loop is ready
        self.relay_node.loop_ready.wait()

        # run LaptopClient's async start method
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.relay_node.async_start())

        print("Starting redirect_Beetle_To_RelayNode...")
        self.redirect_Beetle_To_RelayNode()        
    
    def redirect_Beetle_To_RelayNode(self):
        while True:
            data = self.global_queue.get()
            print(f"Data taken: {data} | Queue Size After Taking: {self.global_queue.qsize()}")
            asyncio.run_coroutine_threadsafe(self.relay_node.enqueue_data(data), self.relay_node.loop)
            print(f"Data transferred: {data}")

    def spawn_beetle_threads(self):
        for device_info in beetle_devices:
            beetle = BeetleDevice(device_info["address"], device_info["service_uuid"], device_info["characteristic_uuid"], device_info["name"], self.global_queue)
            thread = threading.Thread(target=beetle.beetle_handler)
            self.beetle_threads.append(thread)
            thread.start()
        
def main():
    beetle = BeetleMain()
    beetle.start()
    beetle.join()

if __name__ == '__main__':
    main()