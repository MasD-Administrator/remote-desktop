import queue
from threading import Thread

class Buffer:
    def __init__(self, network):
        self.network = network
        self.tick = network.tick

        self.buffer = queue.LifoQueue()

    def add(self, data, mode):
        self.buffer.put([data, mode])
        ######
        if not self.network.is_sending:
            self.send()
        else:
            if self.network.is_sending:
                self.send_after_wait()

    def send_after_wait(self):
        while not self.network.is_sending:
            self.send()
            exit()

    def send(self):
        try:
            buffer_unit = self.buffer.get()
            send_data = buffer_unit[0]
            mode = buffer_unit[1]
            self.network.network_send(send_data, mode=mode)
        except IndexError:
            self.is_waiting = False
            print("dont worry: this is just multiple instances trying to work with sel.buffer at the same time, i could user a lock but nah")