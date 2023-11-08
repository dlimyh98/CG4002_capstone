# BACKUP CODE FOR AI_MAIN on U96

import pandas as pd
from ai_MLPClassifier66 import MLPClassifier66
import time
import asyncio
import queue
import threading
import logging

class MainApp(threading.Thread):

    def __init__(self, loop):
        super().__init__()
        self.mlp = MLPClassifier66()
        #self.mlp = CNNClassifier()
        self.input_queue = queue.Queue()
        self.output_queue = queue.Queue()

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
                self.mlp.handle_timeout(6)
                self.mlp.handle_timeout(2)
                # dequeue data from the input_queue 
                # glove [0:7]
                data = self.input_queue.get()
                result = self.mlp.handle_sample(data)
                if result is not None:
                   player_id, action = result
                   self.output_queue.put((player_id, action))
                   logging.info(f"[AI main]: action: {player_id, action}")
                   print(f"[AI main]: Action classification: {player_id, action}")
                # self.mlp.record_sample(data[1:7])
                
            except Exception as e:
                print(f"MainApp error: {e}")

    async def async_start(self):
        self.loop = asyncio.get_event_loop()
        await self.loop.run_in_executor(None, self.start)
        print("AI started.")


if __name__ == '__main__':
    # app = MainApp('../data/spear_raw.csv')
    app = MainApp()
    app.run()
