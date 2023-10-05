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

        # for i in range(50):
        #     self.global_queue.put(i)

        # initialise classes
        self.beetle_simulator = BeetleSimulator(self.global_queue)
        self.loop = asyncio.get_event_loop()
        self.relay_node = LaptopClient(HOSTNAME, REMOTE_BIND_PORT, self.loop)
    
    async def start(self):
        self.beetle_simulator.start()
        asyncio.create_task(self.relay_node.start())
        self.redirect_Beetle_To_RelayNode()
        
            
    def redirect_Beetle_To_RelayNode(self):
        while True:
            try:
                data = self.global_queue.get()
                # print(f"Beetle Data: {data}")
                asyncio.run_coroutine_threadsafe(self.async_put(data), self.relay_node.loop)
                # await self.relay_node.send_queue.put(data)
               
                print(f"Data transferred: {data}")
            except Exception as e:
                print(f"Error: {e}")

    async def async_put(self, data):
        print("enter async_put coroutine")
        await self.relay_node.send_queue.put(data)
        print(self.relay_node.send_queue)

async def main():
    try:
        beetleLaptopPipeline = BeetleLaptopPipeline()
        await beetleLaptopPipeline.start()
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass