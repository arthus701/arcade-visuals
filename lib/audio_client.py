import socket, json


class AudioClient:
    def __init__(self, listen: str, port: int, bufsize: int):
        self.socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM
        )
        self.socket.bind((listen, port))
        self.socket.setblocking(0)

        self.bufsize = bufsize
    
    def update(self) -> dict:
        try:
            while True:
                raw_data = self.socket.recv(self.bufsize)
        except BlockingIOError:
            pass

        return json.loads(raw_data)
        