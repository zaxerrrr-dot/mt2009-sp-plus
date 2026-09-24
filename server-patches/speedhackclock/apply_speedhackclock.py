#!/usr/bin/env python3
"""apply_speedhackclock.py <engine game/src dir> -- Linux/VPS twin of
Apply-SpeedHackClockPatch.ps1 (same replacement, same marker). The move
check of input_main.cpp (CInputMain::Move) disconnected a player whose move
time ran ahead of the server's by more than 2% of the time since the last
handshake - 150 ms after 7 s. On a PC whose Docker/WSL2 clock runs fast and
is stepped back 2-3 s every half minute, that was every player, every half
minute. 5 s of slack now. Applied once; a file without the expected code
stops with an error, changing nothing. Only the line changes, in its own
line ending."""
import os
import sys

MARK = 'MT2009_PLUS_SPEEDHACK_CLOCK_V1'
OLD = '\t\t\telse if (iDelta < -(iServerDelta / 50))\n'
NEW = "\t\t\t// MT2009_PLUS_SPEEDHACK_CLOCK_V1 (server-patches/speedhackclock): 5 s of slack.\n\t\t\t// A Docker/WSL2 clock that runs fast and is stepped back 2-3 s at a time put\n\t\t\t// a player's moves 'in the future' and the 2% margin disconnected him every\n\t\t\t// half minute (SPEEDHACK: DETECTED! ... delta -1500). A real speedhack runs\n\t\t\t// ahead by far more than 5 s.\n\t\t\telse if (iDelta < -(iServerDelta / 50) - 5000)\n"


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    path = os.path.join(sys.argv[1], "input_main.cpp")
    text = open(path, "rb").read().decode("latin-1")
    if MARK in text:
        print("speedhackclock: already applied")
        return
    for old, new in ((OLD.replace("\n", "\r\n"), NEW.replace("\n", "\r\n")), (OLD, NEW)):
        if text.count(old) == 1:
            text = text.replace(old, new, 1)
            break
    else:
        sys.exit("speedhackclock: expected code not found in " + path)
    open(path, "wb").write(text.encode("latin-1"))
    print("speedhackclock: applied")


if __name__ == "__main__":
    main()
