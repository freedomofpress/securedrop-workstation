import os
import select
import errno

BUFFSIZE = 4096

class PipeReader():
    def __init__(self, pipe, cb):
        self._quit = False
        self.pipe = pipe
        self.cb = cb

        try:	
            os.mkfifo(pipe)
        except OSError as oe:
            if oe.errno != errno.EEXIST:
                raise


    def quit(self):
        self._quit = True

    def read(self):
        print "entering read"

        pipe = self.pipe
        cb = self.cb

        fifo = os.open(pipe, os.O_RDONLY | os.O_NONBLOCK)
        poller = select.epoll()
        poller.register(fifo)

        while not self._quit:   
            events = poller.poll(timeout=1)
            for fileno, event in events:     
                if event & select.EPOLLIN:
                    data = os.read(fifo, BUFFSIZE)
                    cb(self, data, None)

                if event & select.EPOLLHUP:
                    poller.unregister(fileno)
                    os.close(fileno)
                    fifo = os.open(pipe, os.O_RDONLY | os.O_NONBLOCK)
                    poller.register(fifo)

                if event & select.EPOLLERR:
                    print "Error while polling."
                    cb(None, "Polling error!")
                    poller.unregister(fileno)
                    os.close(fileno)
                    fifo = os.open(pipe, os.O_RDONLY | os.O_NONBLOCK)
                    print("FIFO opened {}".format(fifo))
                    poller.register(fifo)

def reporter(poller, msg, err):
    print "Got a message: {} (error: {})".format(msg.rstrip(), err)
    if msg.rstrip() == "quit":
        poller.quit()

if __name__ == '__main__':
    reader = PipeReader("mypipe", reporter)
    reader.read()
