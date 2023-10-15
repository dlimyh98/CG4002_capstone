# main class for Ultra96

import asyncio
import json
import logging
from relay_node_server import RelayNodeServer
from eval_client import EvalClient
from visualizer_ultra96 import VisualizerClient
from game_engine import GameEngine

# define constants
RELAY_NODE_SERVER_HOST = '0.0.0.0'
RELAY_NODE_SERVER_PORT = 8080
ULTRA96_SERVER_IP = "127.0.0.1"
SECRET_KEY = "mysecretkey12345"
HANDSHAKE_PASSWORD = "hello"

logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s', 
                    filename='U96main.log',
                    filemode='w')

class Ultra96:
    def __init__(self):

        # initalise classes
        self.relay_node_server = RelayNodeServer(RELAY_NODE_SERVER_HOST, RELAY_NODE_SERVER_PORT)
        self.eval_client = EvalClient(ULTRA96_SERVER_IP, SECRET_KEY, HANDSHAKE_PASSWORD)
        self.visuazlier_client = VisualizerClient()
        self.game_engine = GameEngine()

        self.is_running = True

      
    async def run(self):
        try:
            print("Ultra96 starting...")
            logging.info("Ultra96 starting...")
            await asyncio.gather(
                asyncio.create_task(self.eval_client.run()),
                asyncio.create_task(self.relay_node_server.start()) ,  
                asyncio.create_task(self.visuazlier_client.start()),
                asyncio.create_task(self.outgoing_data_pipeline()),
                asyncio.create_task(self.incoming_data_pipeline())
            )
        except KeyboardInterrupt:
            pass
        finally:
            await self.stop()

    async def outgoing_data_pipeline(self):
        """
        Overall pipeline for outgoing data.

        Source of this data should be from the hardware sensors.
        """
        if not self.is_running:
            return
        
        # spawn all pipeline coroutines
        asyncio.create_task(self.redirect_RelayNode_to_AI())
        asyncio.create_task(self.redirect_AI_to_GameEngine())
        asyncio.create_task(self.redirect_GameEngine_to_EvalClient_and_VisualizerClient())

    async def incoming_data_pipeline(self):
        """
        Overall pipeline for incoming data.

        Source of this data should be from the eval server or the visualizer.
        """
        if not self.is_running:
            return
        
        # spawn all pipeline coroutines
        asyncio.create_task(self.redirect_EvalClient_to_GameEngine())
        asyncio.create_task(self.redirect_Visualizer_to_GameEngine())
        asyncio.create_task(self.redirect_GameEngine_to_RelayNodeServer())

    async def redirect_RelayNode_to_AI(self):
        """
        Redirects data from the Relay Node to the Hardware AI.

        Only packets related to actions should be passed in, 'shoot' can be passed directly to game engine
        """
        if not self.is_running:
            return
        
        loop = asyncio.get_event_loop()

        try:
            while self.is_running:
                data = await self.relay_node_server.receive_queue.get()

                # redirect to AI
        except asyncio.CancelledError:
            return
        except Exception as e:
            print(f"Error: {e}")
    
    async def redirect_AI_to_GameEngine(self):
        #TODO
        return
    
    async def redirect_GameEngine_to_EvalClient_and_VisualizerClient(self):
        #TODO
        return

    async def redirect_EvalClient_to_GameEngine(self):
        #TODO
        return

    async def redirect_Visualizer_to_GameEngine(self):
        #TODO
        return

    async def redirect_GameEngine_to_RelayNodeServer(self):
        #TODO
        return 
    

    # method should be removed upon integration  
    async def redirect_LaptopServer_to_EvalClient(self):
        if not self.is_running:
            return
        try:
            while self.is_running:
                data = await self.relay_node_server.receive_queue.get()

                print(f"[LaptopServer -> EvalClient and VisualizerClient:] {data}")

                await self.eval_client.send_queue.put(data)
                await self.visuazlier_client.send_queue.put(data)
        except asyncio.CancelledError:
            return
        except Exception as e:
            print(f"pipe1 Error: {e}")

    # this should be removed upon integration
    async def redirect_Visualizer_to_LaptopServer(self):
        if not self.is_running:
            return
        try:
            while self.is_running:
                data = await self.visuazlier_client.receive_queue.get()
                print(f"[Visualizer -> LaptopServer:] {data}")
                await self.relay_node_server.send_queue.put(data) 
        except asyncio.CancelledError:
            return
        except Exception as e:
            print(f"pipe2 Error: {e}")

    async def stop(self):
        print("Stopping Ultra96...")
        logging.info("Stopping Ultra96...")
        self.is_running = False

        # close other connections here
        await asyncio.gather(
            await self.eval_client.stop(),
            await self.relay_node_server.stop(),
            await self.visuazlier_client.stop()
        )
        # print a logout message
        print("Ultra96 stopped.")
        logging.info("Ultra96 stopped.")

async def main():
    ultra96 = Ultra96() 
    await ultra96.run()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
