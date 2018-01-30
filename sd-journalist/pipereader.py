#!/usr/bin/python

import os
import select
import errno

BUFFSIZE = 64


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

        pipe = self.pipe
        cb = self.cb

        fifo = os.open(pipe, os.O_RDONLY | os.O_NONBLOCK)
        poller = select.epoll()
        poller.register(fifo)

        while not self._quit:
            events = poller.poll(timeout=1)
            for fileno, event in events:
                if event & select.EPOLLIN:

                    # read at most BUFSIZE bytes from the fifo
                    data = os.read(fifo, BUFFSIZE)

                    # in this application, we never want to read more
                    # than BUFSIZE bytes. writes from our client
                    # should be atomic up to PIPE_BUF byes, which is
                    # greater than our BUF_SIZE (see
                    # https://unix.stackexchange.com/questions/68146/what-are-guarantees-for-concurrent-writes-into-a-named-pipe). So,  # noqa: E501
                    # we can immediately close this filehandle

                    poller.unregister(fileno)
                    os.close(fileno)
                    cb(self, data.rstrip(), None)
                    fifo = os.open(pipe, os.O_RDONLY | os.O_NONBLOCK)
                    poller.register(fifo)

                elif event & select.EPOLLHUP:
                    poller.unregister(fileno)
                    os.close(fileno)

                    fifo = os.open(pipe, os.O_RDONLY | os.O_NONBLOCK)
                    poller.register(fifo)

                elif event & select.EPOLLERR:
                    print "Error while polling."
                    cb(None, "POLLING_ERROR")
                    poller.unregister(fileno)
                    os.close(fileno)
                    fifo = os.open(pipe, os.O_RDONLY | os.O_NONBLOCK)
                    print("FIFO opened {}".format(fifo))
                    poller.register(fifo)
                elif event:
                    print "Totally unhandled event: {}".format(event)
                    cb(None, "POLLING_ERROR")
                    poller.unregister(fileno)
                    os.close(fileno)
                    fifo = os.open(pipe, os.O_RDONLY | os.O_NONBLOCK)
                    poller.register(fifo)


def reporter(poller, msg, err):
    print "Got a message: {} (error: {})".format(msg.rstrip(), err)
    if msg.rstrip() == "quit":
        poller.quit()


if __name__ == '__main__':
    reader = PipeReader("mypipe", reporter)
    reader.read()
