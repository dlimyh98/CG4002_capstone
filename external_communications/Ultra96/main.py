# main class for Ultra96

import asyncio
import json
from laptop_server import LaptopServer
from eval_client import EvalClient
from visualizer_ultra96 import VisualizerClient

# define constants
LAPTOP_SERVER_HOST = '0.0.0.0'
LAPTOP_SERVER_PORT = 8080
ULTRA96_SERVER_IP = "127.0.0.1"
SECRET_KEY = "mysecretkey12345"
HANDSHAKE_PASSWORD = "hello"

class Ultra96:
    def __init__(self):

        # initalise classes
        self.laptop_server = LaptopServer(LAPTOP_SERVER_HOST, LAPTOP_SERVER_PORT)
        self.eval_client = EvalClient(ULTRA96_SERVER_IP, SECRET_KEY, HANDSHAKE_PASSWORD)
        self.visuazlier_client = VisualizerClient()

        self.is_running = True

      
    async def run(self):
        try:
            input("enter to begin:")
            await asyncio.gather(
                asyncio.create_task(self.eval_client.run()),
                asyncio.create_task(self.laptop_server.start()) ,  
                asyncio.create_task(self.visuazlier_client.start()),
                asyncio.create_task(self.redirect_LaptopServer_to_EvalClient()),
                asyncio.create_task(self.redirect_Visualizer_to_LaptopServer())
            )
        except KeyboardInterrupt:
            pass
        finally:
            await self.stop()
              
    async def redirect_LaptopServer_to_EvalClient(self):
        if not self.is_running:
            return
        try:
            while self.is_running:
                data = await self.laptop_server.receive_queue.get()

                if ("stop" in data):
                    await self.stop()
                    break

                print(f"[LaptopServer -> EvalClient and VisualizerClient:] {data}")

                await self.eval_client.send_queue.put(data)
                await self.visuazlier_client.send_queue.put(data)
        except asyncio.CancelledError:
            return
        except Exception as e:
            print(f"pipe1 Error: {e}")
         
            # this part is just for dummy data, it should be removed upon integration
            # if self.isGrenadeAction(data):
            #     await self.eval_client.send_queue.put(data)
            #     await self.visuazlier_client.send_queue.put(self.generate_grenade_msg_for_visualizer())
            # else:
            #     await self.eval_client.send_queue.put(data)
            #     await self.visuazlier_client.send_queue.put(data)
    
    # temporary method to send a custom message to the visualizer_client for a grenade action
    # if data represents a grenade action, return a custom message to be put 
    # def isGrenadeAction(self, data):
    #     parsed_data = json.loads(data)
    #     if parsed_data["action"] == "grenade":
    #         return True
    #     return False
    
    # def generate_grenade_msg_for_visualizer(self):
    #     message = {
    #         "type": "action",
    #         "player_id": "player1", 
    #         "action_type": "grenade",
    #         "target_id": "player2"           
    #     }
    #     return json.dumps(message)

    
    async def redirect_Visualizer_to_LaptopServer(self):
        if not self.is_running:
            return
        try:
            while self.is_running:
                data = await self.visuazlier_client.receive_queue.get()
                print(f"[Visualizer -> LaptopServer:] {data}")
                await self.laptop_server.send_queue.put(data) 
        except asyncio.CancelledError:
            return
        except Exception as e:
            print(f"pipe2 Error: {e}")

    async def stop(self):
        print("Stopping Ultra96...")
        self.is_running = False

        # close other connections here
        await asyncio.gather(
            await self.eval_client.stop(),
            await self.laptop_server.stop(),
            await self.visuazlier_client.stop()
        )
        # print a logout message
        print("Ultra96 stopped.")

async def main():
    ultra96 = Ultra96() 
    await ultra96.run()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
