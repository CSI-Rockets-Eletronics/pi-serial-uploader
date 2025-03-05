import uploader
import struct
import json

delimiter = b"\xAA\x55"  # {0b10101010, 0b01010101}


def parse_packet(packet: bytes) -> str:
    if len(packet) == 16:
        # breakdown of "!qii":
        #   "!": network byte order
        #   "q": long long
        #   "i": int
        ts, st1, st2 = struct.unpack("!qii", packet)
        data = {"ts": ts, "st1": st1, "st2": st2}
        return json.dumps(data)

    raise ValueError(f"Expected packet length 16, got {len(packet)}")


uploader.run("Scientific", delimiter, parse_packet)
