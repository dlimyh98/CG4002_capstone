import serial
import os
import signal
import sys
import psutil
from multiprocessing import Pool
from itertools import repeat
from enum import Enum

ARDUINO_DUMP_NAME = 'arduino_dump.txt'
SERIAL_PORT = '/dev/ttyACM0'
BAUD_RATE = 9600
SAMPLING_WINDOW_SIZE = 32
SENSORS = ["AccX", "AccY", "AccZ", "GyroX", "GyroY", "GyroZ"]

class SENSOR_ENUM(Enum):
    AccX = 0
    AccY = 1
    AccZ = 2
    GyroX = 3
    GyroY = 4
    GyroZ = 5

## Remove previous data dumps, if they exist
def cleanup(dump_name):
    file_path = os.path.join(os.getcwd(), dump_name)

    if os.path.exists(file_path):
        os.remove(file_path)

    return file_path


## Ctrl-C to stop AI data collection
def signal_handler(sig, frame):
    print("\nCtrl-C pressed, stopping AI data collection\n")
    serial_session.close()

def create_termination_handler():
    signal.signal(signal.SIGINT, signal_handler)


## Check if you have enough physical cores
def determine_num_physical_cores():
    num_physical_cores = psutil.cpu_count(logical = False)

    # We only need 6 parallel jobs (AccX, AccY, AccZ, GyroX, GyroY, GyroZ)
    if (num_physical_cores > 6):
        num_physical_cores = 6


# Communicate through COM port to .ino code
def begin_serial_transmission():
    global serial_session
    serial_session = serial.Serial(SERIAL_PORT, BAUD_RATE)

    # Don't dump the first two lines (they are MPU initialization messages)
    # Still useful to tell you if MPU managed to connect successfully via Serial
    print(serial_session.readline().decode("utf-8"))  # "MPU6050 connection successful"
    print(serial_session.readline().decode("utf-8"))  # ">********......>......DMP enabled..."

    return serial_session


## Dump Arduino output .txt file as long as Serial Port is open
def dump_arduino_output(arduino_dump_path):
    packet_counter = 1

    with open(arduino_dump_path, 'w') as arduino_dump:
        while serial_session.isOpen():
            try:
                line = serial_session.readline().decode("utf-8")
                arduino_dump.write(line)
            except:
                print("Stopped serial communication with Arduino\n")
                break

            # Include the 'E' terminating character as well
            if (packet_counter == SAMPLING_WINDOW_SIZE):
                packet_counter = 1
                arduino_dump.write("E\n")
            else:
                packet_counter += 1


def extract_corresponding_data(sampled_data, sensor):
    extracted_reading = ""

    # 'E' is terminating character used in the .ino code
    if (sampled_data == "E\n"):
        extracted_reading = '\n'
    else:
        # Index using commas as seperators
        processed_line = sampled_data.split(",")
        extracted_reading = processed_line[SENSOR_ENUM[sensor].value]

    return extracted_reading


## Worker process
def worker(sensor, sampling_window_data):
    assert(len(sampling_window_data) == SAMPLING_WINDOW_SIZE + 1)
    counter = 1

    for sampled_data in sampling_window_data:
        # Don't read in 'E\n' terminating character
        if (counter != SAMPLING_WINDOW_SIZE+1):
            extracted_reading = extract_corresponding_data(sampled_data, sensor)
            sensor_dump = open(sensor + ".txt", 'a')
            sensor_dump.write(extracted_reading)

        # CSV format, no comma for SAMPLING_WINDOW_SIZEth reading
        if (counter < SAMPLING_WINDOW_SIZE):
            sensor_dump.write(",")
            counter += 1

        sensor_dump.close()



if __name__ == "__main__":
    ############################################## SEQUENTIAL WORK ##############################################
    num_physical_cores = determine_num_physical_cores()

    arduino_dump_path = cleanup(ARDUINO_DUMP_NAME)
    for sensor in SENSORS:
        cleanup(sensor + ".txt")

    create_termination_handler()

    serial_session = begin_serial_transmission()

    dump_arduino_output(arduino_dump_path)

    ############################################## PARALLEL WORK ##############################################
    # Read arduino_dump.txt ---> Fill up Sampling Window ---> Send out Sampling Window to 6 parallel processes
    sampling_window_data = []
    pool = Pool(num_physical_cores)
    with open("arduino_dump.txt", 'r') as arduino_dump:
        for line in arduino_dump:
            sampling_window_data.append(line)

            # Send the 'E' terminating character as well, so +1 to SAMPLING_WINDOW_SIZE
            if (len(sampling_window_data) == SAMPLING_WINDOW_SIZE+1):
                pool.starmap(worker, zip(SENSORS, repeat(sampling_window_data)))
                sampling_window_data = []