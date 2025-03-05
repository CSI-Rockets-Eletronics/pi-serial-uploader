import uploader
import struct
import json
from typing import Any

delimiter = b"\xAA\x55"  # {0b10101010, 0b01010101}


def parse_packet(packet: bytes) -> str:
    if len(packet) == 20:
        # breakdown of "!qiii":
        #   "!": network byte order
        #   "q": long long
        #   "i": int
        ts, t1, t2, t3 = struct.unpack("!qiii", packet)
        data = {"ts": ts, "t1": t1, "t2": t2,"t3": t3}
        return json.dumps(data)

    raise ValueError(f"Expected packet length 20, got {len(packet)}")


def format_message(message: Any) -> bytes:
    sentence = f"<{message}>"
    return sentence.encode("utf-8")


uploader.run("RocketScientific", delimiter, parse_packet, format_message)
