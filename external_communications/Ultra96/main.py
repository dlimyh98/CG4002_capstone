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

BEETLE_ONE_DATA=2
BEETLE_TWO_DATA=3
BEETLE_THREE_DATA=4
BEETLE_FOUR_DATA=5 # Gun Beetle 1
BEETLE_FIVE_DATA=6
BEETLE_SIX_DATA=7 # Gun Beetle 2

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

        self.packet_count = 0

    async def run(self):
        try:
            print("Ultra96 starting...")
            logging.info("Ultra96 starting...")
            await asyncio.gather(
                asyncio.create_task(self.eval_client.run()),
                asyncio.create_task(self.relay_node_server.start()),  
                asyncio.create_task(self.visuazlier_client.start()),
                asyncio.create_task(self.game_engine.async_start()),
                asyncio.create_task(self.ai_predictor.async_start()),

                asyncio.create_task(self.redirect_RelayNode_to_AI_or_GameEngine()),
                asyncio.create_task(self.redirect_AI_to_GameEngine()),

                asyncio.create_task(self.redirect_GameEngine_to_EvalClient()), 
                asyncio.create_task(self.redirect_EvalClient_to_GameEngine()),

                asyncio.create_task(self.redirect_GameEngine_to_Visualizer()),
                asyncio.create_task(self.redirect_Visualizer_to_GameEngine()),
                asyncio.create_task(self.redirect_GameEngine_to_RelayNodeServer()),

                asyncio.create_task(self.display_frequency()) # this should be removed after testing
            )
        except KeyboardInterrupt:
            pass
        except Exception as e:
            logging.error(f"Ultra96 error: {e}")
            print(f"Ultra96 error: {e}")
        finally:
            await self.stop()

    async def display_frequency(self):
        while self.is_running:
            await asyncio.sleep(10)  # sleep for 10 seconds
            avg_per_second = self.packet_count / 10  # calculate average per second
            logging.info(f"[RelayNode->AI/GameEngine]: Average packets received per second over the last 10 seconds: {avg_per_second}")
            print(f"[RelayNode->AI/GameEngine]: Average packets received per second over the last 10 seconds: {avg_per_second}")
            self.packet_count = 0  # reset the packet count

    async def redirect_RelayNode_to_AI_or_GameEngine(self):
        """
        Redirects data from the Relay Node to the Hardware AI.

        Only packets related to actions should be passed in, 'shoot' can be passed directly to game engine
        """
        if not self.is_running:
            return

        try:
            while self.is_running:
                logging.info("[RelayNode->AI/GameEngine]: Enter pipeline.")
                data = await self.relay_node_server.receive_queue.get()

                #print(f"[RelayNode->AI/GameEngine]: queue size: {self.relay_node_server.receive_queue.qsize()}")

                logging.info(f"[RelayNode->AI/GameEngine]: Data from relay node server: {data}")

                self.packet_count += 1

                # glove
                if data[0] == BEETLE_FIVE_DATA or data[0] == BEETLE_ONE_DATA:
                    await self.loop.run_in_executor(None, self.ai_predictor.input_queue.put, data[0:7])
                    logging.info(f"[RelayNode->AI/GameEngine]: Data to AI: {data[0:7]}") 
                
                # player 1 gun
                elif data[0] == BEETLE_FOUR_DATA:
                    await self.loop.run_in_executor(None, self.game_engine.p1_gun_input_queue.put, data[0])
                    logging.info(f"[RelayNode->AI/GameEngine]: P1 Gun data to Game Engine: {data}")

                # player 2 gun
                elif data[0] == BEETLE_SIX_DATA:
                    await self.loop.run_in_executor(None, self.game_engine.p2_gun_input_queue.put, data[0])
                    logging.info(f"[RelayNode->AI/GameEngine]: P2 Gun data to Game Engine: {data}")

                # player 1 vest
                elif data[0] == BEETLE_THREE_DATA:
                    await self.loop.run_in_executor(None, self.game_engine.p1_vest_input_queue.put, data[0])
                    logging.info(f"[RelayNode->AI/GameEngine]: P1 Vest data to Game Engine: {data}")
                
                # player 2 vest
                elif data[0] == BEETLE_TWO_DATA:
                    await self.loop.run_in_executor(None, self.game_engine.p2_vest_input_queue.put, data[0])
                    logging.info(f"[RelayNode->AI/GameEngine]: P2 Vest data to Game Engine: {data}")

                logging.info("[RelayNode->AI/GameEngine]: Exit pipeline")
                
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
                # actions = ["gun",  "web", "grenade",
                #     "portal", "punch", "hammer", "spear", "shield", "reload", "logout"]
                # if data in actions:
                await self.loop.run_in_executor(None, self.game_engine.action_input_queue.put, data)

                logging.info(f"[AI->GameEngine]: Data to GameEngine: {data}")
                logging.info("[AI->GameEngine]: Exit pipeline.")
        except asyncio.CancelledError:
            return
        except Exception as e:
            print(f"[AI->GameEngine]: Error: {e}")

    async def redirect_GameEngine_to_EvalClient(self):
        if not self.is_running:
            return

        try:
            while self.is_running:
                logging.info("[GameEngine->EvalClient]: Enter pipeline.")
                data = await self.loop.run_in_executor(None, self.game_engine.eval_client_output_queue.get)

                await self.eval_client.send_queue.put(data)
                logging.info(f"[GameEngine->EvalClient]: Data to EvalClient: {data}")
                logging.info("[GameEngine->EvalClient]: Exit pipeline.")
        except asyncio.CancelledError:
            return
        except Exception as e:
            print(f"[GameEngine->EvalClient]: Error: {e}")

    
    async def redirect_EvalClient_to_GameEngine(self):
        if not self.is_running:
            return

        try:
            while self.is_running:
                logging.info("[EvalClient->GameEngine]: Enter pipeline.")
                data = await self.eval_client.receive_queue.get()

                await self.loop.run_in_executor(None, self.game_engine.eval_client_input_queue.put, data)
                logging.info(f"[EvalClient->GameEngine]: Data to GameEngine: {data}")
                logging.info("[EvalClient->GameEngine]: Exit pipeline.")
        except asyncio.CancelledError:
            return
        except Exception as e:
            print(f"[EvalClient->GameEngine]: Error: {e}")

    async def redirect_GameEngine_to_Visualizer(self):
        if not self.is_running:
            return

        try:
            while self.is_running:
                logging.info("[GameEngine-Visualizer]: Enter pipeline.")
                data = await self.loop.run_in_executor(None, self.game_engine.visualizer_client_output_queue.get)

                # put into eval client's send_queue instead of piping it back into game engine
                await self.visuazlier_client.send_queue.put(data)
                logging.error(f"[GameEngine->Visualizer]: Data to Visualizer: {data}")
                logging.info("[GameEngine->Visualizer]]: Exit pipeline.")
        except asyncio.CancelledError:
            return
        except Exception as e:
            print(f"[GameEngine->Visualizer]]: Error: {e}")   

    async def redirect_Visualizer_to_GameEngine(self):
        if not self.is_running:
            return

        try:
            while self.is_running:
                logging.info("[Visualizer->GameEngine]: Enter pipeline.")
                data = await self.visuazlier_client.receive_queue.get()

                # reconstruct packet from confirmation to eval client method

                await self.loop.run_in_executor(None, self.game_engine.visualizer_client_input_queue.put, data)
                logging.error(f"[Visualizer->GameEngine]: Data to GameEngine: {data}")
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
                data = await self.loop.run_in_executor(None, self.game_engine.relay_node_server_output_queue.get)

                await self.relay_node_server.send_queue.put(data)
                logging.info(f"[GameEngine->RelayNodeServer]: Data to RelayNodeServer: {data}")
                logging.info("[GameEngine->RelayNodeServer]: Exit pipeline.")
        except asyncio.CancelledError:
            return
        except Exception as e:
            print(f"[GameEngine->RelayNodeServer]: Error: {e}")

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
