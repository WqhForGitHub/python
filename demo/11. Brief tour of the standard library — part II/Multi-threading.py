# ==============================================================================
# 11.4 Multi-threading
# ==============================================================================
# https://docs.python.org/3/tutorial/stdlib2.html#multi-threading

# --- Threading: running tasks in the background ---
import threading
import zipfile

# Threading is a technique for decoupling tasks which are not sequentially
# dependent. Threads can be used to improve the responsiveness of applications
# that accept user input while other tasks run in the background.


class AsyncZip(threading.Thread):
    def __init__(self, infile, outfile):
        super().__init__()
        self.infile = infile
        self.outfile = outfile

    def run(self):
        with zipfile.ZipFile(self.outfile, 'w', zipfile.ZIP_DEFLATED) as f:
            f.write(self.infile)
        print('Finished background zip of:', self.infile)


# The following demonstrates how to run a background task:
# (Uncomment to test — requires 'mydata.txt' to exist)

# background = AsyncZip('mydata.txt', 'myarchive.zip')
# background.start()
# print('The main program continues to run in foreground.')
# background.join()    # Wait for the background task to finish
# print('Main program waited until background was done.')

# --- Synchronization primitives ---
# The threading module provides locks, events, condition variables,
# and semaphores for coordinating threads that share data or resources.
#
# However, the preferred approach is to concentrate all access to a
# resource in a single thread and use the queue module to feed that
# thread with requests from other threads. Applications using Queue
# objects for inter-thread communication are easier to design,
# more readable, and more reliable.

# --- Example: using a Lock to synchronize access ---
import time

lock = threading.Lock()
shared_counter = 0


def increment_counter(n):
    global shared_counter
    for _ in range(n):
        with lock:  # acquire and release the lock automatically
            shared_counter += 1


threads = []
for _ in range(5):
    t = threading.Thread(target=increment_counter, args=(1000,))
    threads.append(t)
    t.start()

for t in threads:
    t.join()

print('Counter value:', shared_counter)  # 5000
