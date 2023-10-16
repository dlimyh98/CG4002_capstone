# main class for Ultra96

import asyncio
import json
import logging
from relay_node_server import RelayNodeServer
from eval_client import EvalClient
from visualizer_ultra96 import VisualizerClient
from game_engine import GameEngine
from ai_main import MainApp

# define constants
RELAY_NODE_SERVER_HOST = '0.0.0.0'
RELAY_NODE_SERVER_PORT = 8080
ULTRA96_SERVER_IP = "127.0.0.1"
SECRET_KEY = "mysecretkey12345"
HANDSHAKE_PASSWORD = "hello"

logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s', 
                    filename='U96main.log',
                    filemode='w')

class Ultra96:
    def __init__(self, loop):

        self.loop = loop

        # initalise classes
        self.relay_node_server = RelayNodeServer(RELAY_NODE_SERVER_HOST, RELAY_NODE_SERVER_PORT)
        self.eval_client = EvalClient(ULTRA96_SERVER_IP, SECRET_KEY, HANDSHAKE_PASSWORD)
        self.visuazlier_client = VisualizerClient()
        self.game_engine = GameEngine()
        self.ai_predictor = MainApp(self.loop)
        self.is_running = True

    async def run(self):
        try:
            print("Ultra96 starting...")
            logging.info("Ultra96 starting...")
            await asyncio.gather(
                asyncio.create_task(self.eval_client.run()),
                asyncio.create_task(self.relay_node_server.start()),  
                asyncio.create_task(self.visuazlier_client.start()),

                # note: add loop.ready = threading.Event() behaviour into ai_predictor so as to suspend other threads from using
                # it until it is actually ready
                asyncio.create_task(self.ai_predictor.async_start()),

                asyncio.create_task(self.redirect_RelayNode_to_AI()),
                asyncio.create_task(self.redirect_AI_to_GameEngine()),
                asyncio.create_task(self.redirect_GameEngine_to_EvalClient_and_VisualizerClient()),

                asyncio.create_task(self.redirect_EvalClient_to_GameEngine()),
                asyncio.create_task(self.redirect_Visualizer_to_GameEngine()),
                asyncio.create_task(self.redirect_GameEngine_to_RelayNodeServer())
                
                # asyncio.create_task(self.outgoing_data_pipeline()),
                # asyncio.create_task(self.incoming_data_pipeline())
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

        try:
            while self.is_running:
                logging.info("[RelayNode->AI]: Enter pipeline.")
                data = await self.relay_node_server.receive_queue.get()

                logging.info(f"[RelayNode->AI]: Data from relay node server: {data}")

                await self.loop.run_in_executor(None, self.ai_predictor.input_queue.put, data)

                logging.info(f"[RelayNode->AI]: Data to AI: {data}")
                logging.info("[RelayNode->AI]: Exit pipeline")
                
        except asyncio.CancelledError:
            return
        except Exception as e:
            print(f"[RelayNode->AI]: Error: {e}")
    
    async def redirect_AI_to_GameEngine(self):
        if not self.is_running:
            return

        try:
            while self.is_running:
                logging.info("[AI->GameEngine]: Enter pipeline.")
                # dequeue output data from AI
                data = await self.loop.run_in_executor(None, self.ai_predictor.output_queue.get)

                await self.loop.run_in_executor(None, self.game_engine.data_input_queue.put, data)

                logging.info(f"[AI->GameEngine]: Data to GameEngine: {data}")
                logging.info("[AI->GameEngine]: Exit pipeline.")
        except asyncio.CancelledError:
            return
        except Exception as e:
            print(f"[AI->GameEngine]: Error: {e}")
    
    async def redirect_GameEngine_to_EvalClient_and_VisualizerClient(self):
        if not self.is_running:
            return

        try:
            while self.is_running:
                logging.info("[GameEngine->EvalClient, VisualizerClient]: Enter pipeline.")
                data = await self.loop.run_in_executor(None, self.game_engine.data_output_queue.get)

                await self.eval_client.send_queue.put(data)
                await self.visuazlier_client.send_queue.put(data)
                logging.info(f"[GameEngine->EvalClient, VisualizerClient]: Data to both clients: {data}")
                logging.info("[GameEngine->EvalClient, VisualizerClient]: Exit pipeline.")
        except asyncio.CancelledError:
            return
        except Exception as e:
            print(f"[GameEngine->EvalClient, VisualizerClient]: Error: {e}")

    async def redirect_EvalClient_to_GameEngine(self):
        if not self.is_running:
            return

        try:
            while self.is_running:
                logging.info("[EvalClient->GameEngine]: Enter pipeline.")
                data = await self.eval_client.receive_queue.get()

                await self.loop.run_in_executor(None, self.game_engine.data_input_queue.put, data)
                logging.info(f"[EvalClient->GameEngine]: Data to GameEngine: {data}")
                logging.info("[EvalClient->GameEngine]: Exit pipeline.")
        except asyncio.CancelledError:
            return
        except Exception as e:
            print(f"[EvalClient->GameEngine]: Error: {e}")

    async def redirect_Visualizer_to_GameEngine(self):
        if not self.is_running:
            return

        try:
            while self.is_running:
                logging.info("[Visualizer->GameEngine]: Enter pipeline.")
                data = await self.visuazlier_client.receive_queue.get()

                await self.loop.run_in_executor(None, self.game_engine.data_input_queue.put, data)
                logging.info(f"[Visualizer->GameEngine]: Data to GameEngine: {data}")
                logging.info("[Visualizer->GameEngine]: Exit pipeline.")
        except asyncio.CancelledError:
            return
        except Exception as e:
            print(f"[Visualizer->GameEngine]: Error: {e}")

    async def redirect_GameEngine_to_RelayNodeServer(self):
        if not self.is_running:
            return

        try:
            while self.is_running:
                logging.info("[GameEngine->RelayNodeServer]: Enter pipeline.")
                data = await self.loop.run_in_executor(None, self.game_engine.data_output_queue.get)

                await self.relay_node_server.send_queue.put(data)
                logging.info(f"[GameEngine->RelayNodeServer]: Data to RelayNodeServer: {data}")
                logging.info("[GameEngine->RelayNodeServer]: Exit pipeline.")
        except asyncio.CancelledError:
            return
        except Exception as e:
            print(f"[GameEngine->RelayNodeServer]: Error: {e}")
    

    # # method should be removed upon integration  
    # async def redirect_LaptopServer_to_EvalClient(self):
    #     if not self.is_running:
    #         return
    #     try:
    #         while self.is_running:
    #             data = await self.relay_node_server.receive_queue.get()

    #             print(f"[LaptopServer -> EvalClient and VisualizerClient:] {data}")

    #             await self.eval_client.send_queue.put(data)
    #             await self.visuazlier_client.send_queue.put(data)
    #     except asyncio.CancelledError:
    #         return
    #     except Exception as e:
    #         print(f"pipe1 Error: {e}")

    # # this should be removed upon integration
    # async def redirect_Visualizer_to_LaptopServer(self):
    #     if not self.is_running:
    #         return
    #     try:
    #         while self.is_running:
    #             data = await self.visuazlier_client.receive_queue.get()
    #             print(f"[Visualizer -> LaptopServer:] {data}")
    #             await self.relay_node_server.send_queue.put(data) 
    #     except asyncio.CancelledError:
    #         return
    #     except Exception as e:
    #         print(f"pipe2 Error: {e}")

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
    loop = asyncio.get_event_loop()
    ultra96 = Ultra96(loop) 
    await ultra96.run()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
