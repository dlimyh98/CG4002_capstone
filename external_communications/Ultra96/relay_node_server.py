# class implementation for relay node server (on Ultra96)
import asyncio
import logging
import struct

HOST = '0.0.0.0' # listen on all network interfaces
PORT = 8080

BEETLE_ONE_DATA=2
BEETLE_TWO_DATA=3
BEETLE_THREE_DATA=4
BEETLE_FOUR_DATA=5 # Gun Beetle 1
BEETLE_FIVE_DATA=6
BEETLE_SIX_DATA=7 # Gun Beetle 2

class RelayNodeServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port

        self.send_queue = asyncio.Queue()
        self.receive_queue = asyncio.Queue()

        self.server = None
        self.is_running = True

        self.send_task = None

        self.connected_clients = set() # store connected client addresses

        self.packet_count = 0

    async def display_frequency(self):
        while self.is_running:
            await asyncio.sleep(10)  # sleep for 10 seconds
            avg_per_second = self.packet_count / 10  # calculate average per second
            print(f"Average packets received per second over the last 10 seconds: {avg_per_second}")
            self.packet_count = 0  # reset the packet count
    
    async def handle_client(self, reader, writer):
        client_address = writer.get_extra_info('peername')

        if client_address in self.connected_clients:
            print(f"Relay Node {client_address} is already connected. Rejecting connection...")
            logging.error(f"Relay Node {client_address} is already connected. Rejecting connection...")
            return

        print(f"Accepted connection from {client_address}")
        logging.info(f"Accepted connection from {client_address}")  
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
                message = message.encode()
                #message_len = str(len(message))
                #encoded_message = bytes(message_len, encoding='utf8') + b'_' + message.encode("utf8")
                writer.write(message)
                logging.info(f"[RelayNodeServer]: MESSAGE: {message}")
                await writer.drain()
                await asyncio.sleep(0)
        except Exception as e:
            print(f"Error: {e}")

    
    async def receive_message(self, reader):
        try:
            while self.is_running:
                data = await reader.read(20)
                #print(f"data received: {data}")
                if not data:
                    break

                self.packet_count += 1

                decoded_data = self.decode_message(data)
                #print(decoded_data)
                await self.receive_queue.put(decoded_data)
                await asyncio.sleep(0)
        except Exception as e:
            print(f"Error: {e}")
    
    def decode_message(self, data):
        try:
            pkt_id = data[0]
            # glove beetle 2
            if (pkt_id == BEETLE_ONE_DATA):
                pkt_data = struct.unpack('=BbbbhhhHBBBBI', data)
                
                return pkt_data [0:7]

            # vest beetle 1
            elif (pkt_id == BEETLE_TWO_DATA):
                pkt_data = struct.unpack('=BHHHHHHHBI', data)
                return pkt_data [0:2]

            elif (pkt_id == BEETLE_THREE_DATA):
                pkt_data = struct.unpack('=BHHHHHHHBI', data)
                
                return pkt_data

            # Gun Beetle 1 No Ack
            elif (pkt_id == BEETLE_FOUR_DATA):
                pkt_data = struct.unpack('=BHHHHHHHBI', data)
                
                return pkt_data [0:3]
           
            # Glove Beetle 1
            elif (pkt_id == BEETLE_FIVE_DATA):
                pkt_data = struct.unpack('=BbbbhhhHBBBBI', data)
                return pkt_data
            
            # Gun Beetle 2 No ack
            elif (pkt_id == BEETLE_SIX_DATA):
                pkt_data = struct.unpack('=BHHHHHHHBI', data)
                
                return pkt_data  
            else:
                pass

        except struct.error as e:
            print(f"Struct cannot be unpacked: {e}")
        except AssertionError as e:
            print("CRC validation failed.")
        except Exception as e:
            print(f"Unhandled Exception: {e}")

    async def start(self):
        # wait for a connection
        # three params: callback, host, port
        # callback funtion: called whenever a new client connection is established
            print("Relay Node server starting:")
            logging.info("Relay Node server starting:")
            self.server = await asyncio.start_server(self.handle_client, self.host, self.port)

            # frequency_display_task = asyncio.create_task(self.display_frequency())

            try: 
                async with self.server:
                    print(f"Relay Node server listening on {self.host}:{self.port}")
                    logging.info(f"Relay Node server listening on {self.host}:{self.port}")
                    await self.server.serve_forever()
            except asyncio.CancelledError:
                print("Relay Node server cancelled")
                return
            except Exception as e:
                print(f"Relay Node server error: {e}")
                logging.error(f"Relay Node server error: {e}")

    async def stop(self):
        if not self.is_running:
            return
        self.is_running = False
        if self.send_task:
            self.send_task.cancel()
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            print("Realy Node server stopped.")


def main():
    relay_node_server = RelayNodeServer(HOST, PORT)
    asyncio.run(relay_node_server.start())


if __name__ == '__main__':
    main()

