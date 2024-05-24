#!/usr/bin/env python3

import socket
import random
import time
import json

UPDATE_RATE = 60

PORT = 46497

CLIENTS = [ ("127.0.0.1", 46498) ]

BILLION = 1000000000

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(("", PORT))

    while True:
        start_time = time.perf_counter_ns()

        # figure out some data
        rms = random.uniform(0.0, 1.0)
        freq_cats = [[random.uniform(0.0, 1.0), random.uniform(0.0, 1.0), random.uniform(0.0, 1.0)], [random.uniform(0.0, 1.0), random.uniform(0.0, 1.0), random.uniform(0.0, 1.0)]]

        for client in CLIENTS:
            raw_msg = json.dumps({ "rms": rms, "freq_cats": freq_cats }).encode("utf-8")
            server_socket.sendto(raw_msg, client)

        delta = time.perf_counter_ns() - start_time
        if delta < BILLION / UPDATE_RATE:
            time.sleep(((BILLION / UPDATE_RATE) - delta) / BILLION)
        else:
            print(f"Framerate dropped below {UPDATE_RATE}")


if __name__ == "__main__":
    main()
