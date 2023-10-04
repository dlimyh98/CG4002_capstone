import serial
import os
import glob
import signal
import psutil
import argparse
from multiprocessing import Pool
from itertools import repeat
from enum import Enum

SERIAL_PORT = '/dev/ttyACM0'
BAUD_RATE = 9600
SAMPLING_WINDOW_SIZE = 32
DATA_DUMPS_FOLDER_NAME = "data_dumps"
COMMON_ARDUINO_DUMP_FILE_NAME = 'arduino_dump.txt'
SENSORS = ["AccX", "AccY", "AccZ", "GyroX", "GyroY", "GyroZ"]

class SENSOR_ENUM(Enum):
    AccX = 0
    AccY = 1
    AccZ = 2
    GyroX = 3
    GyroY = 4
    GyroZ = 5


## User input
def parse_commands():
    # Setup CMD line commands
    parser = argparse.ArgumentParser(description='Collects AI data')
    parser.add_argument('-n', required=True, help='Input your name', nargs=1,
                        choices = ['alwin', 'damien', 'shawn', 'silin', 'yitching'])
    parser.add_argument('-a', required=True, help='Which action are you doing', nargs=1,
                        choices = ['fist', 'grenade', 'hammer', 'portal', 'reload', 'shield', 'spear', 'spiderweb', 'unique'])

    # Parse the commands
    args = parser.parse_args()
    return args


## Wipe contents of <action_name>/<user_name>, to prepare for fresh data collection
def wipe(action_name, user_name):
    folder_path = os.path.join(os.getcwd(), DATA_DUMPS_FOLDER_NAME, action_name, user_name)
    files = glob.glob(folder_path + '/*.txt')

    # Note that this won't remove subdirectories. But we didn't create any subdirectories anyway
    for file in files:
        os.remove(file)

    return folder_path


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
def dump_arduino_output(folder_path):
    packet_counter = 1

    arduino_dump_file_path = folder_path + '/' + COMMON_ARDUINO_DUMP_FILE_NAME

    with open(arduino_dump_file_path, 'w') as arduino_dump:
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
def worker(sensor, sampling_window_data, folder_path):
    assert(len(sampling_window_data) == SAMPLING_WINDOW_SIZE + 1)
    counter = 1

    for sampled_data in sampling_window_data:
        # Don't read in 'E\n' terminating character
        if (counter != SAMPLING_WINDOW_SIZE+1):
            extracted_reading = extract_corresponding_data(sampled_data, sensor)
            sensor_file_path = folder_path + '/' + sensor + ".txt"
            sensor_dump = open(sensor_file_path, 'a')
            sensor_dump.write(extracted_reading)

        # CSV format, no comma for SAMPLING_WINDOW_SIZEth reading
        if (counter < SAMPLING_WINDOW_SIZE):
            sensor_dump.write(",")
            counter += 1

        sensor_dump.close()



if __name__ == "__main__":
    ############################################## SEQUENTIAL WORK ##############################################
    ## Parse user commands
    args = parse_commands()
    action_name = args.a[0]
    user_name = args.n[0]

    ## Determine num PHYSICAL cores (for parallelizing work later)
    num_physical_cores = determine_num_physical_cores()

    ## Wipe out <action_name>/<user_name> subfolder, to prepare for fresh data collection
    folder_path = wipe(action_name, user_name)

    ## Using SIGINT for our program termination
    create_termination_handler()

    ## Begin communication with Uno
    serial_session = begin_serial_transmission()

    ## Dump Serial.prints() from Uno into .txt file
    dump_arduino_output(folder_path)

    ############################################## PARALLEL WORK ##############################################
    # Read arduino_dump.txt ---> Fill up Sampling Window ---> Send out Sampling Window to 6 parallel processes
    sampling_window_data = []
    pool = Pool(num_physical_cores)
    arduino_dump_file_path = folder_path + '/' + COMMON_ARDUINO_DUMP_FILE_NAME

    with open(arduino_dump_file_path, 'r') as arduino_dump:
        for line in arduino_dump:
            sampling_window_data.append(line)

            # Send the 'E' terminating character as well, so +1 to SAMPLING_WINDOW_SIZE
            if (len(sampling_window_data) == SAMPLING_WINDOW_SIZE+1):
                pool.starmap(worker, zip(SENSORS, repeat(sampling_window_data), repeat(folder_path)))
                sampling_window_data = []