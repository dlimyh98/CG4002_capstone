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
        self.input_queue = queue.Queue()
        self.output_queue = queue.Queue()
        self.mlp = MLPClassifier()

        self.loop = loop    
        self.loop_ready = threading.Event()

    def run(self):
        asyncio.set_event_loop(self.loop)
        self.loop_ready.set()
        self.loop.run_until_complete(self.async_start())
        self.loop.run_forever()

    def start(self):
        while True:
            try:
                # dequeue data from the input_queue
                data = self.input_queue.get()
                action = self.mlp.handle_sample(data)
                if action is not None:
                    print(action)
                    self.output_queue.put(action)
                
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

