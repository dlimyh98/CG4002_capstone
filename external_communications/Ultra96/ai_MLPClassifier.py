from pynq import Overlay
from pynq import allocate
import pynq.lib.dma
import numpy as np
from numpy import mean
import pandas as pd
import logging
from scipy.stats import skew, kurtosis
from scipy.signal import find_peaks
from numpy import mean, std, sqrt, percentile

class MLPClassifier66:
    NO_INPUT_FEATURES = 66
    NO_OUTPUT_CLASSES = 10
    window_size = 40
    action_types = ('punch', 'grenade', 'hammer', 'idle', 'logout', 'portal', 'reload', 'shield', 'spear', 'web')

    feature_means = [0.39505844845908605, 121.67149309245484, 15.406482465462274, 63.51040382571732, -0.014851327682788995, -1.0231767156973652, 417.845525824774, 1046.8443721221254, 0.134643995749203, 504.35439713071196, 4.144200350049317, -3.268065887353879, 114.31176939426142, 15.930924548352817, 60.804992693942616, 0.04193391364146981, -0.9554308066149353, 403.8665200867369, 946.6016341609343, 0.1602683315621679, 456.85110324123275, 4.163715003067618, 6.999468650371945, 123.82717853347502, 15.560042507970245, 64.53866365568545, -0.09392576348355718, -1.0286746697001972, 423.7676145968548, 1051.323044609751, 0.13751328374070138, 516.5080292773645, 4.1477132912938455, -51.739638682252924, 3065.6645855472902, 13.87778958554729, 2858.9703460414453, 0.07754265229473827, 2.4209701477875445, 23614.757692687544, 55266.68591473779, 0.15757173219978748, 2303768.546150903, 4.123529057594501, -33.563230605738575, 2705.294102019129, 12.371944739638682, 2355.5441106535604, -0.28468429270854906, 2.3405984601792977, 18489.56898583875, 45904.79015229194, 0.130326780021254, 1309679.4551628055, 4.0676429083592796, 25.05393198724761, 3970.719845908608, 8.883103081827842, 3136.0253088469713, -0.23917034711873292, 1.3401667304643325, 21406.72234204055, 67949.9406040828, 0.09411530286928799, 2045396.225637513, 3.877662691363197]
    feature_std = [34.329009219992834, 30.454344282027773, 4.134760835062803, 9.729701966666987, 0.42775956284400574, 0.4639308457025445, 46.355167308675206, 288.734667975558, 0.15345127818906745, 119.64620747832976, 0.09086845542926374, 26.985189104876763, 29.395805383878983, 3.955428183721632, 9.623996479257888, 0.38317835545700324, 0.6403650469185825, 49.483848299164514, 221.85875713161508, 0.15735712571934063, 106.98911689846734, 0.07708637611814513, 34.96952040714782, 32.95593857657612, 4.1151497955439895, 10.407590354679266, 0.4458017956439681, 0.611177023915691, 50.75128112136688, 302.5901756714422, 0.1524569507533776, 130.64144188020995, 0.0985985286419287, 583.8260798440658, 2063.3232331679483, 4.121615561284401, 1951.0483864430553, 0.9996940731563904, 2.9461518686387125, 16595.069200130798, 35514.311196796014, 0.1365386314639891, 3420987.782752619, 0.12198782850187047, 405.2219041305868, 1754.5915379065937, 4.514471896363786, 1272.1982613979178, 0.9719179335044369, 3.0502070331458313, 10949.36173712862, 23543.993978861923, 0.12605951614613567, 1731205.2756896361, 0.1885302471871054, 461.62158058964667, 2977.6802634349447, 3.896336334354426, 1582.8861720258535, 0.7929695295674536, 2.632108374112157, 12536.47760735016, 31712.23006770512, 0.105504917430208, 2295347.6928921873, 0.2628454839367702]


    def __init__(self, bitstream_path="mlp_design.bit"):
        self.overlay = Overlay(bitstream_path)
        self.dma = self.overlay.axi_dma_0
        self.input_buffer = allocate(shape=(MLPClassifier66.NO_INPUT_FEATURES,), dtype=np.float32)
        self.output_buffer = allocate(shape=(MLPClassifier66.NO_OUTPUT_CLASSES,), dtype=np.float32)
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

    @staticmethod
    def normalize_features(features):
            # Perform normalization
            normalised_feature_row = []
            for i in range(MLPClassifier66.NO_INPUT_FEATURES):
                mean = MLPClassifier66.feature_means[i]
                std = MLPClassifier66.feature_std[i]
                normalised_feature = (features[i] - mean)/std
                normalised_feature_row.append(normalised_feature)

            return normalised_feature_row


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
        print("Action identified: ", MLPClassifier66.action_types[action], ", Confidence: ", confidence)
        return action


    def handle_sample(self, sample):
        # Check for start-of-movement based on "1" sample
        totalAccAbs = abs(sample[3]) + abs(sample[4]) + abs(sample[5])
        if totalAccAbs < 8000 and self.busy == False:
            return None
        elif totalAccAbs >= 8000 and self.busy == False:
            print("[AI]: exceeded threshold")
            self.busy = True
            self.sample_buffer.append(sample)
            return None
        elif self.busy == True:
            self.sample_buffer.append(sample)
            if len(self.sample_buffer) >= self.window_size:
                print("[AI]: starting classification")
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
                return action
            return None


    def record_sample(self, sample):
        # Check for start-of-movement based on "1" sample
        totalAccAbs = abs(sample[3]) + abs(sample[4]) + abs(sample[5])
        if totalAccAbs < 10000 and self.busy == False:
            return
        elif totalAccAbs >= 10000 and self.busy == False:
            self.busy = True
            self.sample_buffer.append(sample)
            return
        elif self.busy == True:
            self.sample_buffer.append(sample)
            if len(self.sample_buffer) >= self.window_size:
                # Take a window and save to a file
                window_data = pd.DataFrame(self.sample_buffer[-self.window_size:], columns=['AccX', 'AccY', 'AccZ', 'GyroX', 'GyroY', 'GyroZ'])
                self.imu_data_df = pd.concat([self.imu_data_df, window_data], ignore_index=True)
                print(window_data)

                # Clear buffer and set busy to false after classification
                self.sample_buffer = []
                self.busy = False
                
                # Write to csv
                self.imu_data_df.to_csv('imu_data.csv', index=False)
            return


