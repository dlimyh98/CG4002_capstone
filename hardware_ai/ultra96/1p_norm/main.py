import pandas as pd
from MLPClassifier66_v2 import MLPClassifier66
import time

class MainApp:

    def __init__(self, csv_file):
        self.mlp = MLPClassifier66()
        self.data_source = pd.read_csv(csv_file, chunksize=1)  # Read one row at a time to simulate streaming

    def run(self):
        for chunk in self.data_source:
            for _, row in chunk.iterrows():
                imu_data = row.tolist()

                # This is for actual classification
                action = self.mlp.handle_sample(imu_data)

                # This is only for recording purpose, not for actual inference
#                self.mlp.record_sample(imu_data)

                if (action != None):
                    print(f"Detected Action: {action}")
                time.sleep(0.01)  # Optional: Sleep to simulate time delay between IMU readings

if __name__ == '__main__':
    app = MainApp('../data/spear_raw.csv')
    app.run()
