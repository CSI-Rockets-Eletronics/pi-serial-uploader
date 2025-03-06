import uploader
import struct
import json

delimiter = b"\xaa\x55"  # {0b10101010, 0b01010101}


def parse_device(packet: bytes) -> str:
    if len(packet) == 24:
        return "Scientific1"
    if len(packet) == 16:
        return "Scientific2"
    raise ValueError(f"Invalid packet length: {len(packet)}")


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

    if len(packet) == 16:
        # breakdown of "<Qff":
        #   "<": little-endian
        #   "Q": uint64_t (8 bytes)
        #   "f": float (4 bytes)
        ts, injector_manifold_1, injector_manifold_2 = struct.unpack("<Qff", packet)
        data = {
            "ts": ts,
            "injector_manifold_1": injector_manifold_1,
            "injector_manifold_2": injector_manifold_2,
        }
        return json.dumps(data)

    raise ValueError(f"Invalid packet length: {len(packet)}")


uploader.run(parse_device, delimiter, parse_packet)
