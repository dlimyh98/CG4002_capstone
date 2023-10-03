# COMMAND: sudo -E env "PATH=$PATH" /home/yitching/capstone/testingEnv/bin/python /home/yitching/capstone/CG4002_capstone/internal_communications/main.py

import threading
from device import BeetleDevice

service_uuid = "0000dfb0-0000-1000-8000-00805f9b34fb"
characteristic_uuid = "0000dfb1-0000-1000-8000-00805f9b34fb"  # Replace with the UUID of your characteristic
beetle_devices = [
    {"address": "D0:39:72:E4:86:9C", "service_uuid": service_uuid, "characteristic_uuid": characteristic_uuid, "name": "b"},
    {"address": "D0:39:72:E4:8C:09", "service_uuid": service_uuid, "characteristic_uuid": characteristic_uuid, "name": "c"},
    {"address": "D0:39:72:E4:86:F8", "service_uuid": service_uuid, "characteristic_uuid": characteristic_uuid, "name": "d"},
    {"address": "D0:39:72:E4:8C:4D", "service_uuid": service_uuid, "characteristic_uuid": characteristic_uuid, "name": "e"}, # Gun Beetle 1
    {"address": "D0:39:72:E4:86:B4", "service_uuid": service_uuid, "characteristic_uuid": characteristic_uuid, "name": "f"}, 
    {"address": "D0:39:72:E4:80:9F", "service_uuid": service_uuid, "characteristic_uuid": characteristic_uuid, "name": "g"}, # Gun Beetle 2
]

def main():
    beetle_threads = []

    for device_info in beetle_devices:
        beetle = BeetleDevice(device_info["address"], device_info["service_uuid"], device_info["characteristic_uuid"], device_info["name"])
        thread = threading.Thread(target=beetle.beetle_handler)
        beetle_threads.append(thread)
        thread.start()

    for thread in beetle_threads:
        thread.join()

if __name__ == "__main__":
    main()
