import struct
from typing import Any

import uploader

delimiter = b"\xaa\x55"  # {0b10101010, 0b01010101}


def parse_packet(packet: bytes):
    if len(packet) == 20:
        # breakdown of "!qiii":
        #   "!": network byte order
        #   "q": long long
        #   "i": int
        ts, t1, t2, t3 = struct.unpack("!qiii", packet)
        data = {"ts": ts, "t1": t1, "t2": t2, "t3": t3}
        return uploader.Record("RocketScientific", data)


def format_message(message: Any):
    sentence = f"<{message}>"
    return sentence.encode("utf-8")


uploader.run(delimiter, parse_packet, {"RocketScientific": format_message})
