import socket
import threading
import struct
import queue
import time

DELTA = 2208988800
OFFSET = 0


class SNTPServer:
    def __init__(self, port, workers=10):
        self.is_working = True
        self.server_port = port

        self.to_send = queue.Queue()
        self.received = queue.Queue()

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('127.0.0.1', self.server_port))

        self.receiver = threading.Thread(target=self.receive_request)
        self.workers = [threading.Thread(target=self.handle_request) for _ in
                        range(workers)]

    def start(self):
        for worker in self.workers:
            worker.setDaemon(True)
            worker.start()
        self.receiver.setDaemon(True)
        self.receiver.start()
        print(f"listening to {self.server_port} port")
        while self.is_working:
            pass

    def handle_request(self):
        while self.is_working:
            try:
                packet, address = self.received.get(block=False)
            except queue.Empty:
                pass
            else:
                if packet:
                    self.sock.sendto(bytes(packet), address)

    def receive_request(self):
        while self.is_working:
            try:
                data, addr = self.sock.recvfrom(1024)
                self.received.put((self.build_packet(), addr))
                print(f'Request:\nIP: {addr[0]}\nPort: {addr[1]}\n')
            except socket.error:
                return

    def stop(self):
        self.is_working = False
        self.receiver.join()
        for w in self.workers:
            w.join()
        self.server.close()

    @staticmethod
    def main(port):
        server = SNTPServer(port)
        try:
            server.start()
        except KeyboardInterrupt:
            server.stop()

    def build_packet(self):
        return struct.pack(">3B b 5I 3Q",
                           (0 << 6 | 4 << 3 | 4),
                           2, 0, 0, 0, 0, 0, 0, 0, 0,
                           self.to_fractional(OFFSET),
                           self.to_fractional(time.time() + DELTA + OFFSET))

    def to_fractional(self, timestamp):
        return int(timestamp * (2 ** 32))


if __name__ == "__main__":
    OFFSET = int(input("Enter offset in seconds\n"))
    SNTPServer.main(123)
