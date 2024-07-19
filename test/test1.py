import mss

with mss.mss() as ss:
    screen = ss.grab(ss.monitors[1])