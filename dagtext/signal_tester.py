# import signals
from collections import deque
from time import time
from contextlib import contextmanager
from pprint import pprint
from itertools import product


class LineItem:
    def __init__(self, signal, sender, **kws):
        self.signal = signal
        self.sender = sender
        for kw in kws:
            setattr(self, kw, kws[kw])


class SignalRecording(deque):
    def __init__(self, signals=None, recording=True):
        self.recording = recording
        self.recievers = {}
        if signals is not None:
            for s in signals:
                self.add_signal(s)

    def start(self):
        self.recording = True

    def stop(self):
        self.recording = False

    def add_signal(self, signal, added_on='right'):
        # create a reciever w/in closure that adds it with the signalname
        def reciever(source, **kws):
            # print('recieving {}, sender:{}, kws:{}'.format(signal, source, kws))
            if self.recording:
                if added_on == 'right':
                    self.append((signal, source, kws))
                elif added_on == 'left':
                    self.appendleft((signal, source, kws))

        self.recievers[signal] = signal.connect(reciever)
        return self

    def replay(self):
        self.stop()
        temprec = SignalRecording()
        for sig in self.recievers:
            temprec.add_signal(sig)
        pprint(list(self), depth=2)
        for i, sourcesenderkws in enumerate(self):
            sigsource, sender, kws = sourcesenderkws
            sigsource.send(sender, **kws)
            # if (i + 1) != len(temprec):
            #     raise NotImplementedError("YOU NEED TO CHECK IF ANY SIGNALS SEND TO EACHOTHER")


def test_recording():
    import blinker
    s1 = blinker.signal('signal a')
    s2 = blinker.signal('signal b')
    s3 = blinker.signal('signal c')
    r = SignalRecording()
    r.add_signal(s1)
    r.add_signal(s2)
    r.add_signal(s3)
    s1.connect(s2.send)
    s2.connect(s3.send)

    @s1.connect
    @s3.connect
    def yay(*args, **kwargs):
        print(args, kwargs)

    s1.send('a', foo=1)
    s2.send('b', foo=2)
    with s2.connected_to(s3.send):
        s1.send('a')
        # r.replay()
        # s2.send('b', foo=2)
        # s1.send('c', foo=3)
        # s2.send('d', foo=4)
        # r.replay()


if __name__ == '__main__':
    test_recording()
