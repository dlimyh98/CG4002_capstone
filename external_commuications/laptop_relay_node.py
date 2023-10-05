import asyncio
import random
import json
import threading

#HOSTNAME = "172.26.190.124" # U96's public IP
HOSTNAME = "127.0.0.1" # for laptop
REMOTE_BIND_IP = "127.0.0.1"
REMOTE_BIND_PORT = 8080

# dummy data
game_state_dict = {
    "p1": {
        "hp": 100,
        "bullets": 6,
        "grenades": 2,
        "shield_hp": 30,
        "deaths": 0,
        "shields": 2
    },
    "p2": {
        "hp": 100,
        "bullets": 6,
        "grenades": 2,
        "shield_hp": 30,
        "deaths": 0,
        "shields": 2
    },
}

possible_actions = ["gun", "shield", "grenade", "reload", "web",
                    "portal", "punch", "hammer", "spear"]


class LaptopClient(threading.Thread):
    def __init__(self, hostname, remote_port):
        super().__init__()
        self.hostname = hostname
        self.remote_port = remote_port      
        self.send_queue = asyncio.Queue()

        self.loop = asyncio.new_event_loop()
        # self.is_running = True
        self.is_connected = False
           

    async def send_message(self, writer):
        try:
            print("relay node send enter")
            while self.is_connected:
                message = await self.send_queue.get()
                print(f"Relay Node: {message}")
                writer.write(message.encode("utf8"))
                await writer.drain()
        except Exception as e:
            print(f"Error: {e}")


    async def receive_message(self, reader):
        try:
            while self.is_connected:
                data = await reader.read(1024)
                if not data:
                    break
                data = data.decode("utf8")
                print(f"Relay node received: {data}")
        except Exception as e:
            print(f"Error: {e}")


    async def start(self):
        while not self.is_connected:
            try:
                reader, writer = await asyncio.open_connection(self.hostname, self.remote_port)
                print(f"Relay node connected at {self.hostname}:{self.remote_port}.")
                self.is_connected = True

                # create tasks for sending and receiving messages
                send_task = asyncio.create_task(self.send_message(writer))
                print("relay node: send_task created")
                receive_task = asyncio.create_task(self.receive_message(reader)) 
                print("relay node: receive task created")  
                # get_user_input_task = asyncio.create_task(self.get_user_input())

                # wait for both tasks to complete
                await asyncio.gather(send_task, receive_task)

            except ConnectionRefusedError:
                print(f"Connection to Relay Node Server at {self.host}:{self.port} failed. Retrying in 5 seconds...")
                await asyncio.sleep(5)
            except KeyboardInterrupt:
                print("Keyboard interrupt detected. Stopping sending of dummy data:")
            except Exception as e:
                print(f"Error: {e}")

    def run(self):
        asyncio.set_event_loop(self.loop)
        asyncio.run(self.start())
    
    # async def get_user_input(self):
    #     while self.is_connected:
    #         loop = asyncio.get_event_loop()
    #         user_input = await loop.run_in_executor(None, input, "Enter something to send a dummy packet:")

    #         # change this to send a json with the action
    #         await self.send_queue.put(self.create_dummy_data(user_input)) 

    # def create_dummy_data(self, input):
    #     if input == "stop":
    #         return json.dumps("stop")
        
    #     if input == "grenade":
    #         action = "grenade"
    #     else:
    #         action = random.choice(possible_actions)

    #     dummy_data = {
    #         "player_id": 1,
    #         "action": action,
    #         "game_state": game_state_dict
    #     }
    #     return json.dumps(dummy_data)

def main():
    laptop_client = LaptopClient(HOSTNAME, REMOTE_BIND_PORT)
    asyncio.run(laptop_client.start())


if __name__ == '__main__':
    main()

