import socket
import json
import numpy as np


class AudioParameters:
    rms_value = 0.0
    rms_limited_value = 0.0
    rms_limit_threshold = 0.0
    low_rms_value = 0.0
    low_rms_limited_value = 0.0
    low_rms_limit_threshold = 0.0
    mid_rms_value = 0.0
    mid_rms_limited_value = 0.0
    mid_rms_limit_threshold = 0.0
    high_rms_value = 0.0
    high_rms_limited_value = 0.0
    high_rms_limit_threshold = 0.0
    kick = False

    def norm_freq(freq: float):
        return np.clip(freq, None, 6e6) / 6e6


class AudioClient:

    PORT = 46498  

    def __init__(self) -> None:
        self.socket = socket.socket(
                socket.AF_INET,
                socket.SOCK_DGRAM,
            )
        self.socket.bind(("0.0.0.0", self.PORT))
        self.socket.setblocking(0)

        self.parameters = AudioParameters()
    
    def get_audio_parameters(self) -> AudioParameters:
        try:
            while True:
                raw_data = self.socket.recv(1024)
                print(raw_data)
        except BlockingIOError:
            pass

        try:
            data = json.loads(raw_data)

            self.parameters.rms_value = data["rms"]["value"]
            self.parameters.rms_limited_value = data["rms"]["limited_value"]
            self.parameters.rms_limit_threshold = data["rms"]["limit_threshold"]
            self.parameters.low_rms_value = data["low_rms"]["value"]
            self.parameters.low_rms_limited_value = data["low_rms"]["limited_value"]
            self.parameters.low_rms_limit_threshold = data["low_rms"]["limit_threshold"]
            self.parameters.mid_rms_value = data["mid_rms"]["value"]
            self.parameters.mid_rms_limited_value = data["mid_rms"]["limited_value"]
            self.parameters.mid_rms_limit_threshold = data["mid_rms"]["limit_threshold"]
            self.parameters.high_rms_value = data["high_rms"]["value"]
            self.parameters.high_rms_limited_value = data["high_rms"]["limited_value"]
            self.parameters.high_rms_limit_threshold = data["high_rms"]["limit_threshold"]
            self.parameters.kick = data["kick"] == 1
        except UnboundLocalError:
            pass

        return self.parameters
