import socket, json
import lib.parameters as default_parameters


class ParametersDict(dict):
    def __getattr__(self, name: str):
        v = self.get(name)
        if v: 
            return v
        
        if hasattr(default_parameters, name):
            return getattr(default_parameters, name)
        
        raise Exception(f"Trying to access an undefined parameter: {name}")

class ParametersClient(dict):

    data = {}

    def __init__(self, listen: str, port: int, bufsize: int):
        self.socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM
        )
        self.socket.bind((listen, port))
        self.socket.setblocking(0)

        self.bufsize = bufsize

    def update(self) -> ParametersDict:
        try:
            while True:
                raw_data = self.socket.recv(self.bufsize)
        except BlockingIOError:
            pass

        try:
            self.data = json.loads(raw_data)
        except UnboundLocalError:
            pass
        
        return ParametersDict(self.data)
