from pynq import Overlay
from pynq import allocate
import pynq.lib.dma
import numpy as np
from numpy import mean
import pandas as pd
from scipy.stats import skew, kurtosis
from scipy.signal import find_peaks
from numpy import mean, std, sqrt, percentile

class MLPClassifier66:
    NO_INPUT_FEATURES = 66
    NO_OUTPUT_CLASSES = 9
    window_size = 50
    action_types = ('fist', 'grenade', 'hammer', 'logout', 'portal', 'reload', 'shield', 'spear', 'spiderweb')


    def __init__(self, bitstream_path="../mlp_design.bit"):
        self.overlay = Overlay(bitstream_path)
        self.dma = self.overlay.axi_dma_0
        self.input_buffer = allocate(shape=(MLPClassifier66.NO_INPUT_FEATURES,), dtype=np.float32)
        self.output_buffer = allocate(shape=(MLPClassifier66.NO_OUTPUT_CLASSES,), dtype=np.float32)
        self.a_sample_buffer = []
        self.b_sample_buffer = []
        self.r_sample_buffer = []
        self.a_busy = False
        self.b_busy = False
        self.r_busy = False
        self.imu_data_df = pd.DataFrame(columns=['AccX', 'AccY', 'AccZ', 'GyroX', 'GyroY', 'GyroZ'])

    def classify(self, features):
        try:
            for i in range(MLPClassifier66.NO_INPUT_FEATURES):
                self.input_buffer[i] = np.float32(features[i])
            self.dma.sendchannel.transfer(self.input_buffer)
            self.dma.recvchannel.transfer(self.output_buffer)
            self.dma.sendchannel.wait()
            self.dma.recvchannel.wait()

            action = np.argmax(self.output_buffer)
            confidence = self.output_buffer[action]
        except Exception as e:
            print("FPGA could not identify action!", e)
        return action


    @staticmethod
    def normalize_meanstd(X):
        mean = [-0.009802083333333333, 0.5060677083333334, 0.873484375, 29.021260416666667, -42.653421875, 29.278453125]
        std = [75.75090977013078, 74.96003834443778, 75.7644421672966, 2481.8559704856957, 2647.357179406958, 3467.583594031161]
        X_norm = np.zeros_like(X, dtype=float)
        for i in range(X.shape[1]):
            X_norm[:, i] = (X[:, i] - mean[i]) / std[i]
        return X_norm        


    @staticmethod
    def extract_features(window):
        features = []
        for col in window.columns:
            # Time domain features
            tmean = np.mean(window[col])
            tstd = np.std(window[col])
            t25percentile = np.percentile(window[col], 25)
            t50percentile = np.percentile(window[col], 50)  # median
            t75percentile = np.percentile(window[col], 75)
            tIQR = t75percentile - t25percentile  # interquartile range
            zero_crossings = np.where(np.diff(np.sign(window[col])))[0].size  # zero-crossings
            tMAD = np.mean(np.abs(window[col] - tmean))
            features.extend([
                t50percentile,
                tIQR,
                zero_crossings,
                tMAD,
                skew(window[col]),
                kurtosis(window[col])
            ])
            # Frequency domain features
            freq_domain = np.fft.rfft(window[col])
            freq_magnitude = np.abs(freq_domain)
            freq_axis = np.fft.rfftfreq(len(window[col]))
            fmean = np.mean(freq_magnitude)
            fmax = np.max(freq_magnitude)
            dominant_freq = freq_axis[np.argmax(freq_magnitude)]
            energy = np.sum(np.square(freq_magnitude)) / 10000  # divided by 100^2
            fsum = np.sum(freq_magnitude)
            entropy = -np.sum((freq_magnitude / fsum) * np.log2(freq_magnitude / fsum + np.finfo(float).eps))  # spectral entropy
            features.extend([
                fmean,
                fmax,
                dominant_freq,
                energy,
                entropy
            ])
        return features


    def handle_sample(self, sample):
        if True:
           totalGyroAbs =  abs(sample[3]) + abs(sample[4]) + abs(sample[5])
           if totalGyroAbs < 8000 and self.a_busy == False:
               return None
           elif totalGyroAbs >= 8000 and self.a_busy == False:
               self.a_busy = True
               self.a_sample_buffer.append(sample)
               return None
           elif self.a_busy == True:
               self.a_sample_buffer.append(sample)
               if len(self.a_sample_buffer) >= self.window_size:
                   window_data = np.array(self.a_sample_buffer[-self.window_size:]).astype(np.float64)
                   normalized_window_data = self.normalize_meanstd(window_data)
                   features = self.extract_features(pd.DataFrame(normalized_window_data))
                   action = self.classify(features)
                   self.a_sample_buffer = []
                   self.a_busy = False
                   return MLPClassifier66.action_types[int(action)]
               return None


    def record_sample(self, sample):
        # Check for start-of-movement based on "1" sample, no need to change for now
        totalAccAbs = abs(sample[3]) + abs(sample[4]) + abs(sample[5])
        if totalAccAbs < 10000 and self.r_busy == False:
            return
        elif totalAccAbs >= 10000 and self.r_busy == False:
            self.r_busy = True
            self.r_sample_buffer.append(sample)
            return
        elif self.busy == True:
            self.r_sample_buffer.append(sample)
            if len(self.r_sample_buffer) >= self.window_size:
                # Take a window and save to a file
                window_data = pd.DataFrame(self.r_sample_buffer[-self.window_size:], columns=['AccX', 'AccY', 'AccZ', 'GyroX', 'GyroY', 'GyroZ'])
                self.imu_data_df = pd.concat([self.imu_data_df, window_data], ignore_index=True)
                print(window_data)

                # Clear buffer and set busy to false after 50 samples
                self.r_sample_buffer = []
                self.busy = False
                
                # Write to csv
                self.imu_data_df.to_csv('imu_data.csv', index=False)
            return


