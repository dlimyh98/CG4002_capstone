# main.py

import pandas as pd
from ai_MLPClassifier import MLPClassifier
import time

class MainApp:

    def __init__(self, csv_file):
        self.mlp = MLPClassifier()
        self.data_source = pd.read_csv(csv_file, chunksize=1)  # Read one row at a time to simulate streaming

    def run(self):
        for chunk in self.data_source:
            for _, row in chunk.iterrows():
                imu_data = row.tolist()
                print(imu_data)
                action = self.mlp.handle_sample(imu_data)
                if action is not None:
                    print(f"Detected Action: {action}")
                time.sleep(0.05)  # Optional: Sleep to simulate time delay between IMU readings

if __name__ == '__main__':
    app = MainApp('../data/fist_raw.csv')
    time.sleep(5)
    app.run()

