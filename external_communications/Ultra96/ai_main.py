# main.py

import pandas as pd
import threading
import asyncio
import time
import queue

from ai_MLPClassifier import MLPClassifier

class MainApp(threading.Thread):

    def __init__(self, loop):
        super().__init__()
        # self.data_source = pd.read_csv(csv_file, chunksize=1)  # Read one row at a time to simulate streaming
        # self.input_queue = queue.Queue()
        self.input_queue = []
        self.output_queue = queue.Queue()
        self.mlp = MLPClassifier(self.input_queue)

        self.loop = loop    

    def run(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.async_start())
        self.loop.run_forever()

    def start(self):
        # for chunk in self.data_source:
        #     for _, row in chunk.iterrows():
        #         imu_data = row.tolist()
        #         print(imu_data)
        #         action = self.mlp.handle_sample(imu_data)
        #         if action is not None:
        #             print(f"Detected Action: {action}")
        #         time.sleep(0.05)  # Optional: Sleep to simulate time delay between IMU readings
        while True:
            try:
                # dequeue data from the input_queue
                print(f"AI Input Queue size: {len(self.input_queue)}")
                action = self.mlp.handle_sample(self.input_queue)
                #imu_data = self.input_queue.get()
                #print(f"imu data: {imu_data}")
                #action = self.mlp.handle_sample(imu_data)
                print(f"Detected action: {action}")
            except Exception as e:
                print(f"MainApp error: {e}")


    async def async_start(self):
        self.loop = asyncio.get_event_loop()
        await self.loop.run_in_executor(None, self.start)
        print("AI started.")

# if __name__ == '__main__':
#     app = MainApp('../data/fist_raw.csv')
#     time.sleep(5)
#     app.run()

