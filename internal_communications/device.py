import struct
from bluepy import btle
from queue import Queue
import time
import keyboard
from rich import print

from states import States
from delegate import MyDelegate
from errors import MaxCRCFailureError


VERIFIED = "v"

class BeetleDevice:

    def __init__(self, address, service_uuid, characteristic_uuid, name):
        self.address = address
        self.service_uuid = service_uuid
        self.characteristic_uuid = characteristic_uuid
        self.name = name
        self.state = States.DISCONNECTED
        self.device = None
        self.delegate = None
        self.start_time = None
        self.packets_to_send = []
        self.full_packet_list = []
        self.current_packet = bytearray()  # Store the current incomplete packet
    
        self.service = None
        self.characteristic = None
        self.total_bytes_received = 0
        self.fragmented_packet_count = 0
        self.updated_bullet_count = 0

        self.handshake_replied = False  
        self.completed_handshake = False
        self.is_pressed = False

    def beetle_handler(self):

        while True:
            try:
                if self.state == States.DISCONNECTED:
                    self.connect_to_beetle()

                elif self.state == States.HANDSHAKING:
                    self.handshake()
                    if self.completed_handshake:
                        self.state = States.READ

                elif self.state == States.READ:
                    self.receive_data(0.1, 0.5)
        
            except btle.BTLEException as e:
                print("BTLEException, restarting connection: ", e)
                self.reset_flags()
                self.reconnect()
            
            except MaxCRCFailureError as e:
                print(e)
                self.reset_flags()
                self.reconnect()


    def connect_to_beetle(self):
        """
        Establishes a Bluetooth Low Energy (BLE) connection with a Beetle device.

        This function connects to a Beetle device with the specified address using the Bluepy library.
        It sets up the BLE peripheral and delegate for handling notifications. It also checks that the
        service_uuid is valid. 

        Sets the state to States.CONNECTED if connection is successful.

        Returns:
            None. 
        """
        try:
            device = btle.Peripheral(self.address)
            self.delegate = MyDelegate(self)
            device.setDelegate(self.delegate)
            self.device=device
            self.verify_serviceuuid()
            self.characteristic = self.service.getCharacteristics(self.characteristic_uuid)[0]
            print(f"Connected to Beetle module at address {self.address}")
            self.state = States.HANDSHAKING

        except btle.BTLEException as e:
            print(f"Connection to {self.address} failed:", e)
            self.state = States.DISCONNECTED
            return
        
        except Exception as e:
            print(f"Error: {e}")
            self.state = States.DISCONNECTED
            return
        
    def verify_serviceuuid(self):
        try:
            self.service = self.device.getServiceByUUID(self.service_uuid)
            self.state = States.CONNECTED
        
        except btle.BTLEException as e:
            print(f"Service with UUID {self.service_uuid} found", e)
            self.state = States.DISCONNECTED

    def initiate_handshake(self, data="h"): 
        """
        Initiates a handshake with the connected Beetle device.

        Args:
            data (str): The data to send as part of the handshake request.

        This function sends a handshake request to the Beetle device's characteristic.

        Returns:
            None
        """
        # characteristic = self.device.getCharacteristics(uuid=self.characteristic_uuid)[0]
        encrypted_data = data.encode('utf-8')
        self.characteristic.write(encrypted_data, withResponse=True)
        self.receive_data(0.1, 0.2)
    
    def complete_handshake(self, data=VERIFIED):
        """
        Completes the handshake process with the Beetle device.

        This function waits for and processes the response from the Beetle device after initiating the handshake.
        It marks the handshake as successful if the expected acknowledgment is received.

        Returns:
            None
        """
        while(not self.handshake_replied):
            pass

        encrypted_data = data.encode('utf-8')
        self.characteristic.write(encrypted_data, withResponse=True)
        self.completed_handshake = True

    def handshake(self, timeout=3):
        self.start_time = time.time()
        print("Initiating Handshake")
        self.initiate_handshake()

        while True:
            if self.handshake_replied:
                break

            if time.time() - self.start_time > timeout:
                print("Handshake Timeout")
                raise btle.BTLEException(message="Handshake Timeout")  

        self.complete_handshake()

    def reset_flags(self):
        self.handshake_replied = False  
        self.completed_handshake = False

    def reconnect(self, retry_delay=5):
        retry_count = 1
        while(True):
            try:
                print(f"Attempting to reconnect to device {self.address}...")
                self.device.disconnect()  # Disconnect if previously connected
                self.state = States.DISCONNECTED
                self.connect_to_beetle()  # Attempt to reconnect
                return
            
            except btle.BTLEException as e:
                print(f"Reconnection attempt failed: {e}")
                retry_count += 1
                time.sleep(retry_delay * retry_count) 
                # time.sleep(retry_delay)
        
    def receive_data(self, polling_interval=1, duration=10000000000):
        self.total_bytes_received = 0
        self.fragmented_packet_count = 0
        self.start_time = time.time()
        end_time = time.time() + duration
        while time.time() < end_time:
            if self.device.waitForNotifications(timeout=polling_interval):
                continue

        elapsed_time = time.time() - self.start_time
        receiving_speed_kbps = (self.total_bytes_received * 8) / 1024 / elapsed_time
        print(f"Receiving Speed: {receiving_speed_kbps:.2f} kbps")
        print(f"Number of fragmented packets per minute: {self.fragmented_packet_count}")

    # future use if packets cannot be dropped
    def send_ack(self, seq_no):
        try:
            # Convert the sequence number to a single byte
            seq_no_byte = struct.pack('B', seq_no)
            
            # Write the byte to the characteristic with response
            self.characteristic.write(seq_no_byte)
            
            print(f"ACK sent for sequence number: {seq_no}")

        except btle.BTLEException as e:
            print(f"Failed to send ACK: {e}")

    def send_ext(self, debounce_interval=10, bullet_key = "space"):
        try:
            start_press = 0

            if keyboard.is_pressed(bullet_key) and not self.is_pressed:
                start_press = time.time()
                self.is_pressed = True
            
            if self.is_pressed:
                # Send 'g' to Arduino
                print("Entered")
                encrypted_data = 'g'.encode('utf-8')
                self.characteristic.write(encrypted_data)
                time.sleep(1)
                print("Sleeping")
                # Simulate getting the updated bullet count from somewhere
                self.updated_bullet_count += 1  # Change this to the actual bullet count
                bullet_count_bytes = struct.pack('B', self.updated_bullet_count)
                
                # Send the bullet count to Arduino without waiting for acknowledgment
                self.characteristic.write(bullet_count_bytes)

                # Reset the flag
                self.is_pressed = False

        except Exception as e:
            self.is_pressed = False
            print(f"Error in send_ext: {e}")
