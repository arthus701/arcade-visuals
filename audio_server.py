import socket
import time
import json

import numpy as np

import pyaudio
import audioop
# import aubio

CHUNK = 1024  # Number of data points to read at a time

RATE = 44100  # Samples per second

UPDATE_RATE = 60

PORT = 46497

CLIENTS = [ ("0.0.0.0", 46498) ]

BILLION = 1000000000


def analyse(buffer_data) -> dict:
    # Calculate the RMS value of each chunk to measure the volume
    rms = audioop.rms(buffer_data, 2)

    data = np.frombuffer(buffer_data, dtype=np.int16)
    # Apply FFT to the audio data to analyze frequency components
    fft_data = np.fft.fft(data)
    frequencies = np.fft.fftfreq(len(fft_data), d=0.1)

    low_freq_peak = mid_freq_peak = high_freq_peak = 0
    low_amp_peak = mid_amp_peak = high_amp_peak = 0
    i = 0
    for freq in frequencies:
        freq = abs(freq * 11025.0)
        if freq <= 0:
            continue

        amp = np.abs(fft_data[i])
        if freq <= 200 and amp > low_amp_peak:
            low_freq_peak = freq
            low_amp_peak = amp
        elif 200 < freq <= 2000 and amp > mid_amp_peak:
            mid_freq_peak = freq
            mid_amp_peak = amp
        elif 2000 < freq <= 20000 and amp > high_amp_peak:
            high_freq_peak = freq
            high_amp_peak = amp

        i = i + 1

    return {
        "rms": rms,
        "low_peak": {
            "freq": low_freq_peak,
            "amp": low_amp_peak
        },
        "mid_peak": {
            "freq": mid_freq_peak,
            "amp": mid_amp_peak
        },
        "high_peak": {
            "freq": high_freq_peak,
            "amp": high_amp_peak
        }
    }


def main():
    # a_tempo = aubio.tempo("default", 2*CHUNK, CHUNK, RATE)
    # a_pitch = aubio.pitch("default", 2*CHUNK, CHUNK, RATE)
    # a_pitch.set_unit("midi")
    # a_pitch.set_tolerance(0.8)

    p = pyaudio.PyAudio()
    stream = p.open(
        # format=pyaudio.paFloat32,
        format=pyaudio.paInt16,
        channels=1,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK,
    )

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(("", PORT))

    while True:
        start_time = time.perf_counter_ns()

        buffer_data = stream.read(CHUNK)
        # signal = np.frombuffer(buffer_data, dtype=np.float32)
        # is_beat = a_tempo(signal)
        # if is_beat:
        #     print("BEET")
        # pitch = a_pitch(signal)[0]
        # confidence = a_pitch.get_confidence()
        # print(f"{pitch} / {confidence}")

        audio_data = analyse(buffer_data)

        for client in CLIENTS:
            raw_msg = json.dumps(audio_data).encode("utf-8")
            try:
                server_socket.sendto(raw_msg, client)
            except OSError as e:
                print(e)
                server_socket.close()
                raise e

        delta = time.perf_counter_ns() - start_time
        if delta < BILLION / UPDATE_RATE:
            time.sleep(((BILLION / UPDATE_RATE) - delta) / BILLION)
        else:
            # print(f"Framerate dropped below {UPDATE_RATE}")
            pass


if __name__ == "__main__":
    while True:
        try:
            main()
        except OSError:
            time.sleep(0.5)
