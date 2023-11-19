import numpy as np
from numpy import mean
import pandas as pd
from scipy.stats import skew, kurtosis
from scipy.signal import find_peaks
from numpy import mean, std, sqrt, percentile
from keras.models import load_model

class MLPClassifier66:
    NO_INPUT_FEATURES = 66
    NO_OUTPUT_CLASSES = 9
    window_size = 50
    action_types = ('fist', 'grenade', 'hammer', 'logout', 'portal', 'reload', 'shield', 'spear', 'spiderweb')


    def __init__(self):
        self.a_2xfifo_buffer = []
        self.b_2xfifo_buffer = []
        self.r_sample_buffer = []
        self.r_busy = False
        self.imu_data_df = pd.DataFrame(columns=['AccX', 'AccY', 'AccZ', 'GyroX', 'GyroY', 'GyroZ'])
        self.model = load_model('mlp_1105.h5')


    @staticmethod
    def normalize_meanstd(X):
        mean = [-2.0990805785123965, -2.2693078512396694, 3.8193698347107436, 29.71384297520661, -151.3491012396694, -252.54415289256198]
        std = [76.00614608672325, 73.58412389501531, 76.88542448849746, 5545.863844354484, 4034.240202940179, 4882.675451187075]
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
            entropy = -np.sum((freq_magnitude / fsum) * np.log2(freq_magnitude / fsum + np.finfo(float).eps))
            features.extend([
                fmean,
                fmax,
                dominant_freq,
                energy,
                entropy
            ])
        return features


    def onset_detection(self, prev_window, curr_window, threshold=1000):
        # previous window
        totalGyroPrevAbs0 = 0;
        totalGyroPrevAbs1 = 0;
        totalGyroPrevAbs2 = 0;
        # current window
        totalGyroCurrAbs0 = 0;
        totalGyroCurrAbs1 = 0;
        totalGyroCurrAbs2 = 0;
        # summation of absolute imu value
        for i in range(self.onset_cmp_size):
            totalGyroPrevAbs0 += abs(prev_window[i][3])
            totalGyroPrevAbs1 += abs(prev_window[i][4])
            totalGyroPrevAbs2 += abs(prev_window[i][5])
            totalGyroCurrAbs0 += abs(curr_window[i][3])
            totalGyroCurrAbs1 += abs(curr_window[i][4])
            totalGyroCurrAbs2 += abs(curr_window[i][5])
        # difference
        gyroDiffAbs0 = (totalGyroCurrAbs0 - totalGyroPrevAbs0) / self.onset_cmp_size
        gyroDiffAbs1 = (totalGyroCurrAbs1 - totalGyroPrevAbs1) / self.onset_cmp_size
        gyroDiffAbs2 = (totalGyroCurrAbs2 - totalGyroPrevAbs2) / self.onset_cmp_size
        # decide
        if (gyroDiffAbs0 + gyroDiffAbs1 + gyroDiffAbs2 > threshold):
            return True
        return False


    def handle_sample(self, sample):
        if sample[0] == 6:
            # buffer full
            if (len(self.a_2xfifo_buffer) == 2*self.window_size):
                # check "mid point" imu reading
                totalGyroAbs = abs(self.a_2xfifo_buffer[self.window_size][3]) + abs(self.a_2xfifo_buffer[self.window_size][4]) + abs(self.a_2xfifo_buffer[self.window_size][5])
                if totalGyroAbs >= 8000:
                    # further check mean of prev window and current window
                    onset = self.onset_detection(self.a_2xfifo_buffer[self.window_size-self.onset_cmp_size:self.window_size], self.a_2xfifo_buffer[self.window_size:self.window_size+self.onset_cmp_size])
                    if onset:
                        curr_window = self.a_2xfifo_buffer[self.window_size:2*self.window_size]
                        window_data = np.array(curr_window[-self.window_size:]).astype(np.float64)
                        print(window_data)
                        normalized_window_data = self.normalize_meanstd(window_data)
                        features = self.extract_features(pd.DataFrame(normalized_window_data))
                        action = np.argmax(self.model.predict(np.array(features).reshape(1, -1)), axis=-1)
                        self.a_2xfifo_buffer = []
                        self.a_2xfifo_buffer.append(sample) 
                        return (1, MLPClassifier66.action_types[int(action)])
                    else:
                        return None
                # if no classification happens, pop first element 
                else:
                    self.a_2xfifo_buffer.append(sample) 
                    self.a_2xfifo_buffer.pop(0)
                    return None
            # buffer not full
            else:
                self.a_2xfifo_buffer.append(sample) 
                return None
        elif sample[0] == 2:
            # buffer full
            if (len(self.b_2xfifo_buffer) == 2*self.window_size):
                # check "mid point" imu reading
                totalGyroAbs = abs(self.b_2xfifo_buffer[self.window_size][3]) + abs(self.b_2xfifo_buffer[self.window_size][4]) + abs(self.b_2xfifo_buffer[self.window_size][5])
                if totalGyroAbs >= 8000:
                    # further check mean of prev window and current window
                    onset = self.onset_detection(self.b_2xfifo_buffer[self.window_size-self.onset_cmp_size:self.window_size], self.b_2xfifo_buffer[self.window_size:self.window_size+self.onset_cmp_size])
                    if onset:
                        curr_window = self.b_2xfifo_buffer[self.window_size:2*self.window_size]
                        window_data = np.array(curr_window[-self.window_size:]).astype(np.float64)
                        print(window_data)
                        normalized_window_data = self.normalize_meanstd(window_data)
                        features = self.extract_features(pd.DataFrame(normalized_window_data))
                        action = np.argmax(self.model.predict(np.array(features).reshape(1, -1)), axis=-1)
                        self.b_2xfifo_buffer = []
                        self.b_2xfifo_buffer.append(sample) 
                        return (1, MLPClassifier66.action_types[int(action)])
                    else:
                        return None
                # if no classification happens, pop first element 
                else:
                    self.b_2xfifo_buffer.append(sample) 
                    self.b_2xfifo_buffer.pop(0)
                    return None
            # buffer not full
            else:
                self.b_2xfifo_buffer.append(sample) 
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

                # Clear buffer and set busy to false after 40 samples
                self.r_sample_buffer = []
                self.busy = False
                
                # Write to csv
                self.imu_data_df.to_csv('imu_data.csv', index=False)
            return


