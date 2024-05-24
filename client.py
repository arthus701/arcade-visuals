#!/usr/bin/env python3

import socket
import random
import time
import json

UPDATE_RATE = 60

PORT = 46498

BILLION = 1000000000

def main():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.bind(("", PORT))
    client_socket.setblocking(0)

    while True:
        # we only measure time to simulate the game engine, which caps out at 60fps
        start_time = time.perf_counter_ns()

        delta = time.perf_counter_ns() - start_time
        if delta < BILLION / UPDATE_RATE:
            time.sleep(((BILLION / UPDATE_RATE) - delta) / BILLION)
        else:
            print(f"Framerate dropped below {UPDATE_RATE}")

        raw_data = client_socket.recv(1024)
        data = json.loads(raw_data)
        print(data["rms"])


if __name__ == "__main__":
    main()
