from enum import Enum

class States(Enum):
    DISCONNECTED = 0
    CONNECTED = 1
    HANDSHAKING = 2
    READ = 3
    WRITE = 4
    WAIT_READ = 5