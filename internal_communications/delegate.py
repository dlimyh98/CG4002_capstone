from bluepy import btle
import struct
from rich import print
from errors import MaxCRCFailureError
import time
from data_manager import DataManager
from data_collector import DataCollector
import logging

ACK = 1
BEETLE_ONE_DATA=2
BEETLE_TWO_DATA=3
BEETLE_THREE_DATA=4
BEETLE_FOUR_DATA=5 # Gun Beetle 1
BEETLE_FIVE_DATA=6
BEETLE_SIX_DATA=7 # Gun Beetle 2
MAX_FAIL_COUNT = 5

data_manager = DataManager()

class MyDelegate(btle.DefaultDelegate):
   
    def __init__(self, beetle_device, send_queue, receive_queue):
        btle.DefaultDelegate.__init__(self)
        self.count = 0
        self.beetle = beetle_device
        self.packet_buffer = bytearray()
        self.seq_no = 0
        self.crc_fail_count = 0
        self.first_crc_fail_time = 0
        self.received_crc_int = 0
        self.calculated_crc = 0
        self.send_queue = send_queue
        self.receive_queue = receive_queue
        self.last_received_time = 0
        self.receive_interval = 2
        
        self.data_collector = DataCollector("Yit Ching", "test")

    def handleNotification(self, cHandle, data):
        # Append data to buffer        
        self.packet_buffer.extend(data)

        if len(self.packet_buffer) % 20 != 0:
            self.beetle.fragmented_packet_count += 1

        if self.is_packet_complete(self.packet_buffer):
            # take out first 20 bytes of packet
            self.process_packet(self.packet_buffer[:20])
            # reset buffer to remaining bytes
            del self.packet_buffer[:20]
        
        if self.beetle.completed_handshake:
            if time.time() - self.last_received_time > self.receive_interval:
                self.beetle.send_ext(self.beetle.name, self.receive_queue)
                self.last_received_time = time.time()

    def process_packet(self, data):
        self.count +=1
        try:
            pkt_id = data[0]
            if (pkt_id == BEETLE_ONE_DATA):
                pkt_data = struct.unpack('=BbbbhhhHBBBBI', data)
                
                if(self.validate_packet(data)):
                
                    self.seq_no = pkt_data[-3]
                    self.beetle.total_bytes_received += 9 #Only data bytes
                    print(f"[red] Beetle One Packet received successfully: {pkt_data}[/red]")
                    self.send_queue.put(data)
                    self.data_collector.store_data(pkt_data[1:7])

            elif (pkt_id == BEETLE_TWO_DATA):
                pkt_data = struct.unpack('=BHHHHHHHBI', data)
                
                if(self.validate_packet(data)):
                
                    self.seq_no = pkt_data[-3]

                    if self.beetle.completed_handshake:
                        self.beetle.send_ack(self.seq_no)

                    print(f"[red] Beetle Two Packet received successfully: {pkt_data}[/red]")
                    self.send_queue.put(data)

            elif (pkt_id == BEETLE_THREE_DATA):
                pkt_data = struct.unpack('=BHHHHHHHBI', data)
                
                if self.validate_packet(data):
                
                    self.seq_no = pkt_data[-3]
                    
                    print(f"[blue] Beetle Three Packet received successfully: {pkt_data}[/blue]")
                    self.send_queue.put(data)

            # Gun Beetle 1 No Ack
            elif (pkt_id == BEETLE_FOUR_DATA):
                pkt_data = struct.unpack('=BHHHHHHHBI', data)
                
                if self.validate_packet(data):

                    self.beetle.total_bytes_received += 2 #Only data bytes

                    self.seq_no = pkt_data[-3]

                    print(f"[purple]Beetle Four Packet received successfully: {pkt_data}[/purple]")
                    self.send_queue.put(data)
           
            # Glove Beetle 1
            elif (pkt_id == BEETLE_FIVE_DATA):
                pkt_data = struct.unpack('=BbbbhhhHBBBBI', data)
                # pkt_data = struct.unpack('=BHHHHHHHBI', data)
                if(self.validate_packet(data)):

                    self.beetle.total_bytes_received += 9 #Only data bytes

                    self.seq_no = pkt_data[-3]

                    print(f"[yellow]Beetle Five Packet received successfully: {pkt_data}[/yellow]")
                    logging.debug(f"Packet 5 data: {data}")
                    self.send_queue.put(data)

            # Gun Beetle 2 No ack
            elif (pkt_id == BEETLE_SIX_DATA):
                pkt_data = struct.unpack('=BHHHHHHHBI', data)
                
                if(self.validate_packet(data)):

                    self.beetle.total_bytes_received += 2 #Only data bytes
                    self.seq_no = pkt_data[-3]

                    print(f"[blue]Beetle Six Packet received successfully: {pkt_data}[/blue]")

                    self.send_queue.put(data)
                    print(f"from beetle:{self.send_queue.qsize()}")
                    
            elif (pkt_id == ACK):
                # added
                if(self.validate_packet(data)):
                    print(f"HANDSHAKE SUCCESS: {data}")
                    self.beetle.handshake_replied = True
            else:
                pass

        except struct.error as e:
            print(f"Struct cannot be unpacked: {e}")
        except AssertionError as e:
            print("CRC validation failed.")
        except btle.BTLEException as e: 
            print(f"Beetle error: {e}") 
        except MaxCRCFailureError as e:
            print(e)
            self.beetle.reset_flags()
            self.beetle.reconnect()
        except Exception as e:
            print(f"Unhandled Exception: {e}")

    def is_packet_complete(self, data):
        return len(data) >= 20
    
    def custom_crc32(self,data):
        crc = 0x00000000
        
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 1:
                    crc = (crc >> 1) ^ 0x04C11DB7
                else:
                    crc >>= 1
        
        return crc & 0xFFFFFFFF
    

    def validate_packet(self, packet):
        self.received_crc_int = struct.unpack("I", packet[16:])[0]
        self.calculated_crc = self.custom_crc32(packet[:-4])
        if(self.received_crc_int == self.calculated_crc):
            self.crc_fail_count = 0
            return True

        else:
            print("CRC Failed")
            print(f"Received full packet: {packet}")
            print(f"Received {self.received_crc_int}")
            print(f"Received data packet: {packet[:-4]}")
            print(f"Calculated {self.calculated_crc}")
            if time.time() - self.first_crc_fail_time > 3:
                self.first_crc_fail_time = 0
                self.crc_fail_count = 0

            if self.crc_fail_count == 0:
                self.first_crc_fail_time = time.time()
            
            self.crc_fail_count += 1
        
            if self.crc_fail_count > MAX_FAIL_COUNT:
                self.crc_fail_count = 0
                self.packet_buffer.clear()
                raise MaxCRCFailureError("Max CRC failure reached")

            return False

