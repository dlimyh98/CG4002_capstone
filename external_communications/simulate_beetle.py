# simulate six beetles transmitting data into a central queue using threading
import threading
import time
import queue

class BeetleSimulator():
    def __init__(self, global_queue):
        self.num_beetles = 6
        self.beetle_threads = []
        self.global_queue = global_queue

    def simulate_beetle(self, beetle_id):
        while True:
            # create a simple packet
            packet = (beetle_id, 1)

            # put the packet into the queue
            self.global_queue.put(packet)
            print(f"Packet: {packet} | Queue Size: {self.global_queue.qsize()}")

            # delay for 0.5 seconds before sending the next packet
            time.sleep(2)
    
    def start(self):
        for beetle_id in range(1, self.num_beetles + 1):
            thread = threading.Thread(target=self.simulate_beetle, args=(beetle_id,))
            thread.daemon = True
            self.beetle_threads.append(thread)
            thread.start()
            print(f"Thread {beetle_id} started.")
    
        # for thread in self.beetle_threads:
        #     thread.join()

# def main():
#     beetleSimulator = BeetleSimulator()
#     beetleSimulator.start()

# if __name__ == '__main__':
#     try:
#         main()
#     except KeyboardInterrupt:
#         pass