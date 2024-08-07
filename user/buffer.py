import time
from threading import Thread

class Buffer:
    def __init__(self, network):
        self.network = network
        self.tick = network.tick
        self.buffer = []

        Thread(target=self.continuous_send).start()

    def add(self, data, mode):
        self.buffer.insert(0, [data, mode])

    def continuous_send(self):
        while True:
            if self.network.connected_to_server:
                len_of_buffer = len(self.buffer)

                if len_of_buffer > 0:
                    buffer_unit = self.buffer[-1]
                    send_data = buffer_unit[0]
                    mode = buffer_unit[1]
                    self.network.network_send(send_data, mode=mode)
                    self.buffer.pop(-1)

            time.sleep(self.tick)
