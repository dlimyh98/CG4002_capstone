from pynq import Overlay
from pynq import allocate
import pynq.lib.dma
import numpy as np
from numpy import mean
import pandas as pd
from scipy.stats import skew, kurtosis
from numpy import mean, std, sqrt, percentile

class MLPClassifier30:
    NO_INPUT_FEATURES = 30
    NO_OUTPUT_CLASSES = 9
    window_size = 40
    overlap = 20
    action_types = ('punch', 'grenade', 'hammer', 'logout', 'portal', 'reload', 'shield', 'spear', 'web')

    feature_means = [-1.9966783216783215, 73.38459640694794, 75.54115569058169, -63.33435314685315, -1.0303851915618074, -1.3773164335664336, 72.39155688072135, 74.00232825762268, -60.93181818181818, -1.0459333145096694, 5.2488636363636365, 77.29582371752126, 79.91763614851985, -61.10445804195804, -1.1349091683677284, -91.04427447552449, 3459.4794665839577, 3493.804302414613, -1440.3732517482517, 2.583795799078547, -213.45668706293705, 3562.6123104498006, 3590.980739001803, -1466.3981643356644, 2.561213920008102, 52.98999125874126, 4668.908917723914, 4683.883199268134, -1895.6647727272727, 0.6189788771492792]

    feature_std = [17.543091177268618, 9.084308759409353, 8.517554947573977, 25.938593370221177, 0.43931446711358824, 15.203855860349583, 7.728833166656481, 7.521460356069555, 21.640161021066188, 0.3562967031186588, 19.40700993477209, 8.489723487509966, 7.962423720756025, 29.852052622312453, 0.48435229256823364, 511.7372110820126, 2469.6724200501762, 2475.9588247400593, 1270.9772997643204, 2.990884826346434, 539.11254616067, 2052.2803104129543, 2084.43008167832, 1408.8924295610925, 2.6509963160796235, 415.40397906683813, 2119.2354906122146, 2127.495187083009, 1973.0897980567356, 1.6160582835737587]   

    def __init__(self, bitstream_path="mlp_design.bit"):
        self.overlay = Overlay(bitstream_path)
        self.dma = self.overlay.axi_dma_0
        self.input_buffer = allocate(shape=(MLPClassifier30.NO_INPUT_FEATURES,), dtype=np.float32)
        self.output_buffer = allocate(shape=(MLPClassifier30.NO_OUTPUT_CLASSES,), dtype=np.float32)
        self.sample_buffer = []
        self.busy = False
        self.imu_data_df = pd.DataFrame(columns=['AccX', 'AccY', 'AccZ', 'GyroX', 'GyroY', 'GyroZ'])

    @staticmethod
    def extract_features(window):
        features = []
        for col in window.columns:
            # Time domain features
            tmean = np.mean(window[col])
            tstd = np.std(window[col])
            trms = np.sqrt(np.mean(np.square(window[col])))
            t25percentile = np.percentile(window[col], 25)
            tkurtosis = kurtosis(window[col])
            features.extend([
                tmean,
                tstd,
                trms,
                t25percentile,
                tkurtosis
            ])
        return features

    @staticmethod
    def normalize_features(features):
            # Perform normalization
            normalised_feature_row = []
            for i in range(MLPClassifier30.NO_INPUT_FEATURES):
                mean = MLPClassifier30.feature_means[i]
                std = MLPClassifier30.feature_std[i]
                normalised_feature = (features[i] - mean)/std
                normalised_feature_row.append(normalised_feature)

            return normalised_feature_row


    def classify(self, features):
        try:
            for i in range(MLPClassifier30.NO_INPUT_FEATURES):
                self.input_buffer[i] = np.float32(features[i])
            self.dma.sendchannel.transfer(self.input_buffer)
            self.dma.recvchannel.transfer(self.output_buffer)
            self.dma.sendchannel.wait()
            self.dma.recvchannel.wait()

            action = np.argmax(self.output_buffer)
            confidence = self.output_buffer[action]
        except Exception as e:
            print("FPGA could not identify action!", e)
        print("Action identified: ", MLPClassifier30.action_types[action], ", Confidence: ", confidence)
        return action


    def handle_sample(self, sample):
        # Check for start-of-movement based on "1" sample
        totalAccAbs = abs(sample[3]) + abs(sample[4]) + abs(sample[5])
        if totalAccAbs < 10000 and self.busy == False:
            return None
        elif totalAccAbs >= 10000 and self.busy == False:
            self.busy = True
            self.sample_buffer.append(sample)
            return None
        elif self.busy == True:
            self.sample_buffer.append(sample)
            if len(self.sample_buffer) >= self.window_size:
                # Take a windowed data from sample_buffer
                window_data = pd.DataFrame(self.sample_buffer[-self.window_size:])
                # Extract and normalize feature
                features = self.extract_features(window_data)
                normalized_features = self.normalize_features(features)
                # Classify action
                action = self.classify(normalized_features) 
                # Clear buffer and set busy to false after classification
                self.sample_buffer = []
                self.busy = False
                return MLPClassifier30.action_types[action]
            return None
    
    def record_sample(self, sample):
        # Check for start-of-movement based on "1" sample
        totalAccAbs = abs(sample[3]) + abs(sample[4]) + abs(sample[5])
        if totalAccAbs < 10000 and self.busy == False:
            return
        elif totalAccAbs >= 10000 and self.busy == False:
            self.busy = True
            self.sample_buffer.append(sample)
            print(len(self.sample_buffer), sample)
            return
        elif self.busy == True:
            self.sample_buffer.append(sample)
            print(len(self.sample_buffer), sample)
            if len(self.sample_buffer) >= self.window_size:
                # Take a window and save to a file
                window_data = pd.DataFrame(self.sample_buffer[-self.window_size:], columns=['AccX', 'AccY', 'AccZ', 'GyroX', 'GyroY', 'GyroZ'])
                self.imu_data_df = pd.concat([self.imu_data_df, window_data], ignore_index=True)
                # print(window_data)

                # Clear buffer and set busy to false after classification
                self.sample_buffer = []
                self.busy = False
                
                # Write to csv
                self.imu_data_df.to_csv('logout.csv', index=False)
            return

