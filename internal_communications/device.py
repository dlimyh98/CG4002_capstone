import struct
from bluepy import btle
from queue import Queue
import time
from rich import print
import logging
import threading
from states import States
from delegate import MyDelegate
from errors import MaxCRCFailureError
# from data_collector import DataCollector


VERIFIED = "v"
PLAYER_ONE_BULLETS = 6
PLAYER_TWO_BULLETS = 6
PLAYER_ONE_HEALTH = 100
PLAYER_TWO_HEALTH = 100
player_bullets_lock = threading.Lock()
player_health_lock = threading.Lock()

class BeetleDevice:

    def __init__(self, address, service_uuid, characteristic_uuid, name, send_queue, receive_queue):
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
        self.updated_bullet_count = 6

        self.handshake_replied = False  
        self.completed_handshake = False
        self.is_pressed = False

        self.send_queue = send_queue
        self.receive_queue = receive_queue
        # self.data_collector = DataCollector("Yitching2", "test2")
        self.last_glove_receive_time = 0

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
                    print(f"receive queue size:{self.receive_queue.qsize()}")
                    # if not the glove beetles then check for updates to be sent to hardware
                    if self.name != "b1" and self.name != "b5":
                        self.send_ext(self.name, self.receive_queue)

                    if self.name == "b1" or self.name == "b5":
                        self.characteristic.write('e'.encode('utf-8'))

                    # if (self.name == "b1" or self.name == "b5") and (time.time() - self.last_glove_receive_time > 40):
                    #     raise btle.BTLEException("No glove data reconnecting...")
                        
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
            self.delegate = MyDelegate(self, self.send_queue, self.receive_queue)
            device.setDelegate(self.delegate)
            self.device=device
            self.verify_serviceuuid()
            self.characteristic = self.service.getCharacteristics(self.characteristic_uuid)[0]
            logging.info(f"Connected to Beetle module at address {self.address}")
            self.state = States.HANDSHAKING

        except btle.BTLEException as e:
            logging.info(f"Connection to {self.address} failed: {e}")
            self.state = States.DISCONNECTED
            return
        
        except Exception as e:
            logging.error(f"Error: {e}")
            self.state = States.DISCONNECTED
            return
        
    def verify_serviceuuid(self):
        try:
            self.service = self.device.getServiceByUUID(self.service_uuid)
            self.state = States.CONNECTED
        
        except btle.BTLEException as e:
            logging.error(f"Service with UUID {self.service_uuid} found {e}")
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
        logging.info("Initiating Handshake")
        self.initiate_handshake()

        while True:
            if self.handshake_replied:
                break

            if time.time() - self.start_time > timeout:
                logging.info("Handshake Timeout")
                raise btle.BTLEException(message="Handshake Timeout")  

        self.complete_handshake()

    def reset_flags(self):
        self.handshake_replied = False  
        self.completed_handshake = False

    def reconnect(self, retry_delay=5):
        retry_count = 1
        while(True):
            try:
                logging.info(f"Attempting to reconnect to device {self.address}...")
                self.device.disconnect()  # Disconnect if previously connected
                self.state = States.DISCONNECTED
                self.connect_to_beetle()  # Attempt to reconnect
                return
            
            except btle.BTLEException as e:
                logging.info(f"Reconnection attempt failed: {e}")
                retry_count += 1
                time.sleep(retry_delay * retry_count) 
        
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
        logging.info(f"Receiving Speed: {receiving_speed_kbps:.2f} kbps")
        logging.info(f"Number of fragmented packets per minute: {self.fragmented_packet_count}")

    # future use if packets cannot be dropped
    def send_ack(self, seq_no):
        try:
            # Convert the sequence number to a single byte
            seq_no_byte = struct.pack('B', seq_no)
            
            # Write the byte to the characteristic with response
            self.characteristic.write(seq_no_byte)
            
            logging.info(f"ACK sent for sequence number: {seq_no}")

        except btle.BTLEException as e:
            logging.info(f"Failed to send ACK: {e}")
    
    def send_ext(self, beetle_device_id, receive_queue):
        # If received message meant for gun beetles i..e., bullet count
        # Assume format ("b", 1, 4) || ("b", 2, 3)
        # Assume format ("h", 1, 30) || ("h", 2, 40)
        global PLAYER_ONE_BULLETS, PLAYER_TWO_BULLETS, PLAYER_ONE_HEALTH, PLAYER_TWO_HEALTH
        try:
            print("Entered send Ext")

            if receive_queue.empty():
                print(f"Entered empty receive queue: {receive_queue.qsize()}")
            else:            
                # check what data it is
                current_data = receive_queue.get()

                if len(current_data) != 3:
                    return
                
                logging.debug(f"Send Ext:{current_data}")
                data_type, player_num, data_content = current_data[0], current_data[1], current_data[2]
                # remove junk data
                print(f"data type: {data_type}")
                print(f"beetle device id: {beetle_device_id}")
                print(f"player num: {player_num}")

                if data_type != "b" and data_type != "h":
                    print("entered removing junk")
                    return       
                    
                with player_bullets_lock:
                    if data_type == "b" and player_num == 1:
                        PLAYER_ONE_BULLETS = data_content
                    if data_type == "b" and player_num == 2:
                        PLAYER_TWO_BULLETS = data_content
                with player_health_lock:
                    if data_type == "h" and player_num == 1:
                        PLAYER_ONE_HEALTH = data_content
                    if data_type == "h" and player_num == 2:
                        print(f"updated {data_content}")
                        PLAYER_TWO_HEALTH = data_content

            if beetle_device_id == "b4" :
                logging.debug(f"Entered gun update for player 1 {PLAYER_ONE_BULLETS}")
                encrypted_flag = 'g'.encode('utf-8') # Send "send data flag" to arduino
                self.characteristic.write(encrypted_flag)
                encrypted_updated_bullet_count = struct.pack('B', PLAYER_ONE_BULLETS)
                self.characteristic.write(encrypted_updated_bullet_count)
        
            if beetle_device_id == "b6":
                logging.debug(f"Entered gun update for player 2: {PLAYER_TWO_BULLETS}")
                encrypted_flag = 'g'.encode('utf-8') # Send "send data flag" to arduino
                self.characteristic.write(encrypted_flag)
                encrypted_updated_bullet_count = struct.pack('B', PLAYER_TWO_BULLETS)
                self.characteristic.write(encrypted_updated_bullet_count)

            if beetle_device_id == "b2":
                logging.debug(f"Entered health update for player 1 {PLAYER_ONE_HEALTH}")
                encrypted_flag = 'g'.encode('utf-8')
                self.characteristic.write(encrypted_flag)
                encrypted_updated_health = struct.pack('B', PLAYER_ONE_HEALTH)
                self.characteristic.write(encrypted_updated_health)
            
            if beetle_device_id == "b3":
                logging.debug(f"Entered health update for player 2 {PLAYER_TWO_HEALTH}")
                encrypted_flag = 'g'.encode('utf-8')
                self.characteristic.write(encrypted_flag)
                encrypted_updated_health = struct.pack('B', PLAYER_TWO_HEALTH)
                self.characteristic.write(encrypted_updated_health)
                
        except Exception as e:
            print(f"No data retrieved, {e}")

