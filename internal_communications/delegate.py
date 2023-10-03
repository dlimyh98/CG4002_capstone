from bluepy import btle
from queue import Queue
import struct
from rich import print
from errors import MaxCRCFailureError
import time

ACK = 1
BEETLE_ONE_DATA=2
BEETLE_TWO_DATA=3
BEETLE_THREE_DATA=4
BEETLE_FOUR_DATA=5 # Gun Beetle 1
BEETLE_FIVE_DATA=6
BEETLE_SIX_DATA=7 # Gun Beetle 2
MAX_FAIL_COUNT = 10

class MyDelegate(btle.DefaultDelegate):
   
    def __init__(self, beetle_device):
        btle.DefaultDelegate.__init__(self)
        self.count = 0
        self.beetle = beetle_device
        self.packet_buffer = b""
        self.seq_no = 0
        self.crc_fail_count = 0

    def handleNotification(self, cHandle, data):
        # Append data to buffer
        self.packet_buffer += data
        # self.beetle.total_bytes_received += len(data)
        # calculation should be number of data bytes and not the full 20 bytes
        if len(self.packet_buffer) % 20 != 0:
            self.beetle.fragmented_packet_count += 1

        if self.is_packet_complete(self.packet_buffer):
            # take out first 20 bytes of packet
            self.process_packet(self.packet_buffer[:20])
            # reset buffer to remaining bytes
            self.packet_buffer = self.packet_buffer[20:]
        
        if self.beetle.completed_handshake:
            self.beetle.send_ext()

    def process_packet(self, data):
        self.count +=1
        try:
            pkt_id = data[0]
            if (pkt_id == BEETLE_ONE_DATA):
                pkt_data = struct.unpack('=BHHHHHHHBI', data)
                
                self.validate_packet(data)
                
                self.seq_no = pkt_data[-3]

                print(f"[red] Beetle One Packet received successfully: {pkt_data}[/red]")

            elif (pkt_id == BEETLE_TWO_DATA):
                pkt_data = struct.unpack('=BHHHHHHHBI', data)
                
                self.validate_packet(data)
                
                self.seq_no = pkt_data[-3]

                if self.beetle.completed_handshake:
                    self.beetle.send_ack(self.seq_no)

                print(f"[red] Beetle Two Packet received successfully: {pkt_data}[/red]")

            elif (pkt_id == BEETLE_THREE_DATA):
                pkt_data = struct.unpack('=BHHHHHHHBI', data)
                
                self.validate_packet(data)
                
                self.seq_no = pkt_data[-3]
                
                print(f"[blue] Beetle Three Packet received successfully: {pkt_data}[/blue]")

            # Gun Beetle 1 No Ack
            elif (pkt_id == BEETLE_FOUR_DATA):
                pkt_data = struct.unpack('=BHHHHHHHBI', data)
                
                self.validate_packet(data)

                self.beetle.total_bytes_received += 2 #Only data bytes

                self.seq_no = pkt_data[-3]

                print(f"[purple]Beetle Four Packet received successfully: {pkt_data}[/purple]")

            # Simulate stop n wait
            elif (pkt_id == BEETLE_FIVE_DATA):
                pkt_data = struct.unpack('=BHHHHHHHBI', data)
                
                self.validate_packet(data)

                self.beetle.total_bytes_received += 12 #Only data bytes

                self.seq_no = pkt_data[-3]
                if self.beetle.completed_handshake:
                    self.beetle.send_ack(self.seq_no)

                print(f"[yellow]Beetle Five Packet received successfully: {pkt_data}[/yellow]")

            # Gun Beetle 2 No ack
            elif (pkt_id == BEETLE_SIX_DATA):
                pkt_data = struct.unpack('=BHHHHHHHBI', data)
                
                self.validate_packet(data)

                self.beetle.total_bytes_received += 2 #Only data bytes

                self.seq_no = pkt_data[-3]

                print(f"[blue]Beetle Six Packet received successfully: {pkt_data}[/blue]")

            elif (pkt_id == ACK):
                # added
                self.validate_packet(data)
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
        received_crc_int = struct.unpack("i", packet[16:])[0]
        calculated_crc = self.custom_crc32(packet[:-4])
        if(received_crc_int == calculated_crc):
            return

        else:
            self.crc_fail_count += 1
        
            if self.crc_fail_count > MAX_FAIL_COUNT:
                self.crc_fail_count = 0
                self.packet_buffer = b""
                raise MaxCRCFailureError("Max CRC failure reached")

            raise AssertionError()

