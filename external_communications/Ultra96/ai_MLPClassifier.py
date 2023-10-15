from pynq import Overlay
from pynq import allocate
import pynq.lib.dma
import numpy as np
from numpy import mean
import pandas as pd

class MLPClassifier:
    NO_INPUT_FEATURES = 30
    NO_OUTPUT_CLASSES = 6
    window_size = 40
    overlap = 20
    
    def __init__(self, bitstream_path="../mlp_old.bit"):
        self.overlay = Overlay(bitstream_path)
        self.dma = self.overlay.axi_dma_0
        self.input_buffer = allocate(shape=(self.NO_INPUT_FEATURES,), dtype=np.float32)
        self.output_buffer = allocate(shape=(self.NO_OUTPUT_CLASSES,), dtype=np.float32)
        self.sample_buffer = []

    @staticmethod
    def extract_features(window):
        features = []
        # Time domain features
        for col in window.columns:
            features.extend([
                window[col].mean(),
                window[col].std(),
                window[col].mad(),
                window[col].min(),
                window[col].max()
#                np.sum(window[col]**2)
            ])
            # Frequency domain features
#            fft_values = np.abs(np.fft.fft(window[col]))
#            top_fft_vals = sorted(fft_values, reverse=True)[:5]
#            features.extend(top_fft_vals)
        return features

    def classify(self, features):
        try:
            for i in range(len(features)):
                self.input_buffer[i] = features[i]
            self.dma.sendchannel.transfer(self.input_buffer)
            self.dma.recvchannel.transfer(self.output_buffer)
            self.dma.sendchannel.wait()
            self.dma.recvchannel.wait()
            action = np.argmax(self.output_buffer)
            confidence = self.output_buffer[action]
        except Exception as e:
            print("FPGA could not identify action!", e)
        print("Action identified: ", action, ", Confidence: ", confidence)
        return action
    
    def process_data(self, data):
        features_list = []
        for start in range(0, len(data) - self.window_size + 1, self.overlap):
            window = data.iloc[start:start+self.window_size]
            features = self.extract_features(window)
            features_list.append(features)
        return features_list


    def handle_sample(self, sample):
        """
        Handles a single IMU data sample, adding it to the buffer. 
        If the buffer has sufficient data for a window, extract features and classify.
        """
        self.sample_buffer.append(sample)

        # Check if sample_buffer has enough samples for a window
        if len(self.sample_buffer) >= self.window_size:
            window_data = pd.DataFrame(self.sample_buffer[-self.window_size:])
            features = self.extract_features(window_data)
            action = self.classify(features)
        
            # For 50% overlap, remove half of the window size from the beginning of the buffer
            self.sample_buffer = self.sample_buffer[-self.window_size//2:]

            return action

        return None

