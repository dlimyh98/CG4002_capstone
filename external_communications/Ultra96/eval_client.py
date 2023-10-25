# class implementation for eval_client

import asyncio
import base64
import logging

from Crypto.Random import get_random_bytes
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

# hardcoded sample packets to send
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

sample_message_data = {
    "player_id": 1,
    "action": "gun",
    "game_state": game_state_dict
}

sample_message_data2 = {
    "player_id": 1,
    "action": "shield",
    "game_state": game_state_dict
}

class EvalClient:
    def __init__(self, server_ip, secret_key, handshake_password):
        self.server_ip = server_ip
        self.secret_key = secret_key
        self.handshake_password = handshake_password

        self.send_queue = asyncio.Queue()
        self.receive_queue = asyncio.Queue()

        self.reader = None
        self.writer = None

        self.send_task = None
        self.receive_task = None

        self.is_running = True


    async def send_message(self, writer):
        while self.is_running:

            # wait for a message to be placed into the queue
            message = await self.send_queue.get()
            
            encrypted_message = self.encrypt_message(message)
            message_len = str(len(encrypted_message))
            encoded_message = bytes(message_len, encoding='utf8') + b'_' + encrypted_message
            writer.write(encoded_message)
            await writer.drain()
            await asyncio.sleep(0)


    async def receive_message(self, reader):
        try:
            while self.is_running:
                # message length followed by '_' followed by message content
                data = b''
                while not data.endswith(b'_'):
                    _d = await reader.read(1)
                    if not _d:
                        data = b''
                        print("break")
                        break
                    data += _d
                if len(data) == 0:
                    print("Eval Client: no data length received.")
                    logging.debug("Eval Client: no data length received.")
                    break
                data = data.decode("utf8")
                length = int(data[:-1])

                data = b''
                while len(data) < length:
                    _d = await reader.read(length - len(data))
                    if not _d:
                        data = b''
                        break
                    data += _d
                if len(data) == 0:
                    print("no message received")
                    logging.debug("Eval Client: no message received")
                    break
                msg = data.decode("utf8")
                await self.receive_queue.put(msg)
                # print("[EvalServer -> EvalClient:]" + msg)
                logging.info("[EvalServer -> EvalClient:]" + msg)
        except ConnectionResetError:
            print("Connection reset.")
            return
        except asyncio.TimeoutError:
            print("no further messages")
            return
               

    # set up socket connection
    async def run(self):
        server_port = int(input("Enter port number:"))

        # connect to server
        self.reader, self.writer = await asyncio.open_connection(self.server_ip, server_port)

        logging.info(f"Connected to eval_server at {self.server_ip}:{server_port}.")

        # create tasks for sending and receiving messages
        self.send_task = asyncio.create_task(self.send_message(self.writer))
        self.receive_task = asyncio.create_task(self.receive_message(self.reader))

        # send handshake
        await self.send_queue.put(self.handshake_password)
        print("EvalClient: sent handshake.")
        logging.info("EvalClient: Sent handshake.")
        
        # wait for both tasks to complete
        #await asyncio.gather(self.send_task, self.receive_task)
    

    async def stop(self):
        self.is_running = False
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
        if self.reader:
            self.reader.feed_eof()
        if self.send_task:
            self.send_task.cancel()
        if self.receive_task:
            self.receive_task.cancel()
        print("eval client stopped.")
        logging.info("Eval Client stopped.")

        
    def encrypt_message(self, plaintext):
        encoded_secret_key = bytes(self.secret_key, encoding="utf8")
        iv = get_random_bytes(16)
        cipher = AES.new(encoded_secret_key, AES.MODE_CBC, iv)
        padded_message = pad(plaintext.encode('utf8'), AES.block_size)
        ciphertext = iv + cipher.encrypt(padded_message)
        return base64.b64encode(ciphertext)
        
