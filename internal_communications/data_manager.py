import queue

class DataManager:
    def __init__(self):
        self.send_data_queue = queue.Queue()

    def put_data(self, deviceId, data):
        # print(f"Data put into queue from: {deviceId}")
        self.send_data_queue.put(data)

    def get_data(self):
        return self.send_data_queue.get()