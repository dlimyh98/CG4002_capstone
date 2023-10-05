# class implementation for laptop server (on Ultra96)
import asyncio

HOST = '0.0.0.0' # listen on all network interfaces
PORT = 8080

class LaptopServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port

        self.send_queue = asyncio.Queue()
        self.receive_queue = asyncio.Queue()

        self.server = None
        self.is_running = True

        self.send_task = None

        self.connected_clients = set() # store connected client addresses
    
    async def handle_client(self, reader, writer):
        client_address = writer.get_extra_info('peername')

        if client_address in self.connected_clients:
            print(f"Relay Node {client_address} is already connected. Rejecting connection...")
            return

        print(f"Accepted connection from {client_address}")  
        self.connected_clients.add(client_address)

        try:
            self.send_task = asyncio.create_task(self.send_message(writer))
            while True:
                message = await self.receive_message(reader)
                if not message:
                    break
                print(f"Received: {message}")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.connected_clients.remove(client_address)


    async def send_message(self, writer): 
        try:
            while self.is_running:
                message = await self.send_queue.get()
                message_len = str(len(message))
                encoded_message = bytes(message_len, encoding='utf8') + b'_' + message.encode("utf8")
                writer.write(encoded_message)
                await writer.drain()
                await asyncio.sleep(0)
        except Exception as e:
            print(f"Error: {e}")

    
    async def receive_message(self, reader):
        try:
            while self.is_running:
                data = await reader.read(1024)
                if not data:
                    break
                data = data.decode("utf8")
                await self.receive_queue.put(data)
                await asyncio.sleep(0)
        except Exception as e:
            print(f"Error: {e}")

    
    async def start(self):
        # wait for a connection
        # three params: callback, host, port
        # callback funtion: called whenever a new client connection is established
            print("Laptop server starting:")
            self.server = await asyncio.start_server(self.handle_client, self.host, self.port)
            try: 
                async with self.server:
                    print(f"Laptop server listening on {self.host}:{self.port}")
                    await self.server.serve_forever()
            except asyncio.CancelledError:
                print("Laptop server cancelled")
                return
            except Exception as e:
                print(f"Laptop server error: {e}")

    async def stop(self):
        if not self.is_running:
            return
        self.is_running = False
        if self.send_task:
            self.send_task.cancel()
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            print("Laptop server stopped.")


def main():
    laptop_server = LaptopServer(HOST, PORT)
    asyncio.run(laptop_server.start())


if __name__ == '__main__':
    main()

