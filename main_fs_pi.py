import uploader
import struct
import json

delimiter = b"\xAA\x55"  # {0b10101010, 0b01010101}


def parse_packet(packet: bytes) -> str:
    if len(packet) == 24:
        # breakdown of "<Qffff":
        #   "<": little-endian
        #   "Q": uint64_t (8 bytes)
        #   "f": float (4 bytes)
        ts, lox_upper, lox_lower, gn2_manifold_1, gn2_manifold_2 = struct.unpack(
            "<Qffff", packet
        )
        data = {
            "ts": ts,
            "lox_upper": lox_upper,
            "lox_lower": lox_lower,
            "gn2_manifold_1": gn2_manifold_1,
            "gn2_manifold_2": gn2_manifold_2,
        }
        return json.dumps(data)

    raise ValueError(f"Expected packet length 24, got {len(packet)}")


uploader.run("Scientific", delimiter, parse_packet)
