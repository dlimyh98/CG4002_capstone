# simulates the transfer between Beetles and Laptop
import asyncio 
import threading 
import queue
from simulate_beetle import BeetleSimulator
from laptop_relay_node import LaptopClient

HOSTNAME = "127.0.0.1"
REMOTE_BIND_PORT = 8080

class BeetleLaptopPipeline:
    def __init__(self):
        self.global_queue = queue.Queue()
        self.beetle_simulator = BeetleSimulator(self.global_queue)
        self.relay_node = LaptopClient(HOSTNAME, REMOTE_BIND_PORT)

    def start(self):
        self.beetle_simulator.start()
        self.relay_node.start()

        # Wait for the event to signal the loop is ready
        self.relay_node.loop_ready.wait()

        # Run the LaptopClient's asynchronous start method
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

def main():
    try:
        beetleLaptopPipeline = BeetleLaptopPipeline()
        beetleLaptopPipeline.start()
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
