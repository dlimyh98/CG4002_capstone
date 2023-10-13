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
    def __init__(self, hostname, remote_port, loop):
        super().__init__()
        self.hostname = hostname
        self.remote_port = remote_port      
        self.send_queue = asyncio.Queue()
        self.receive_queue = asyncio.Queue()
        self.is_connected = False
        self.loop = loop

    def run(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.async_start())
        self.loop.run_forever()

    async def send_message(self, writer):
        while self.is_connected:
            try:
                message = self.send_queue.get_nowait()
                print(f"Relay Node: {message}")
                str_message = ",".join(map(str, message))
                writer.write(str_message.encode("utf8"))
                await writer.drain()
            except asyncio.QueueEmpty:
                print("Queue is empty, waiting for more data...")
                await asyncio.sleep(1)

    async def receive_message(self, reader):
        while self.is_connected:
            data = await reader.read(1024)
            if not data:
                break
            received_message = data.decode("utf8")
            tuple_message = tuple(map(int, received_message.split(",")))
            print(f"Relay node received: {tuple_message}")

    async def async_start(self):
        while not self.is_connected:
            try:
                reader, writer = await asyncio.open_connection(self.hostname, self.remote_port)
                print(f"Relay node connected at {self.hostname}:{self.remote_port}.")
                self.is_connected = True
                
                # Start the tasks after connecting
                # asyncio.create_task(self.send_message(writer))
                # asyncio.create_task(self.receive_message(reader))

                await asyncio.gather(
                    asyncio.create_task(self.send_message(writer)),
                    asyncio.create_task(self.receive_message(reader)),
                    asyncio.create_task(self.send_kb_input_to_beetle())
                )

            except ConnectionRefusedError:
                print(f"Connection to Relay Node Server at {self.hostname}:{self.remote_port} failed. Retrying in 5 seconds...")
                await asyncio.sleep(5)
            except KeyboardInterrupt:
                print("Keyboard interrupt detected. Stopping...")
            except Exception as e:
                print(f"Error: {e}")

    async def enqueue_data(self, data):
        await self.send_queue.put(data)
    
    async def dequeue_data(self):
        data = await self.receive_queue.get()
        print(f"dequeued data: {data}")
        return data

    async def send_kb_input_to_beetle(self):
        loop = asyncio.get_event_loop()
        while self.is_connected:
            try:
                user_input = await loop.run_in_executor(None, input, ("Enter something to send tuple to beetles:"))
                message = self.create_dummy_beetle_data()
                if message:
                    print(message)
                    await self.receive_queue.put(message)
                    print(self.receive_queue.qsize())
            except Exception as e:
                print(f"Error while getting user input: {e}")
    
    def create_dummy_beetle_data(self):
        return ('b', 1)

    # async def get_user_input(self):
    #     loop = asyncio.get_event_loop()  # Get the loop reference once
    #     while self.is_connected:
    #         try:
    #             user_input = await loop.run_in_executor(None, input, "Enter something to send a dummy packet:")
                
    #             # Assuming create_dummy_data is a method that processes the user input 
    #             # and returns the desired message format for sending.
    #             message = self.create_dummy_data(user_input)
    #             if message:  # Only put the message in the queue if it's valid
    #                 await self.send_queue.put(message)
    #         except Exception as e:
    #             print(f"Error while getting user input or processing it: {e}")

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


    # async def start(self):
    #     print("Starting LaptopClient...")
    #     while not self.is_connected:
    #         print("Attempting to connect...")
    #         try:
    #             reader, writer = await asyncio.open_connection(self.hostname, self.remote_port)
    #             print(f"Relay node connected at {self.hostname}:{self.remote_port}.")
    #             self.is_connected = True

    #         except ConnectionRefusedError:
    #             print(f"Connection to Relay Node Server at {self.hostname}:{self.remote_port} failed. Retrying in 5 seconds...")
    #             await asyncio.sleep(5)
    #         except KeyboardInterrupt:
    #             print("Keyboard interrupt detected. Stopping sending of dummy data:")
    #         except Exception as e:
    #             print(f"Error: {e}")

    #     print("Connected successfully!")

    #     # Once connected, start the tasks
    #     send_task = asyncio.create_task(self.send_message(writer))
    #     receive_task = asyncio.create_task(self.receive_message(reader))
    #     # get_input_task = asyncio.create_task(self.get_user_input())

    #     #await asyncio.gather(send_task, receive_task)

def main():
    laptop_client = LaptopClient(HOSTNAME, REMOTE_BIND_PORT)
    asyncio.run(laptop_client.async_start())


if __name__ == '__main__':
    main()

######################################################################################################################

    # async def get_user_input(self):
    #     loop = asyncio.get_event_loop()  # Get the loop reference once
    #     while self.is_connected:
    #         try:
    #             user_input = await loop.run_in_executor(None, input, "Enter something to send a dummy packet:")
                
    #             # Assuming create_dummy_data is a method that processes the user input 
    #             # and returns the desired message format for sending.
    #             message = self.create_dummy_data(user_input)
    #             if message:  # Only put the message in the queue if it's valid
    #                 await self.send_queue.put(message)
    #         except Exception as e:
    #             print(f"Error while getting user input or processing it: {e}")

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