#!/usr/bin/env python

import datetime
import pipereader
import sd_process_display


def poller_cb(poller, msg, err):
    longer = "(Not a known message)"
    msg = msg.strip()

    if msg in sd_process_display.messages:
        longer = sd_process_display.messages[msg]

    print "[{}] {}: {}".format(datetime.datetime.now(), msg, longer)


reader = pipereader.PipeReader("sdfifo", poller_cb)

reader.read()
