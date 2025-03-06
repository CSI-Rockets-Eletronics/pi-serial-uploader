import struct

import uploader

delimiter = b"\xaa\x55"  # {0b10101010, 0b01010101}


def parse_packet(packet: bytes):
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
        return uploader.Record("FsLoxGn2Transducers", data)

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
        return uploader.Record("FsInjectorTransducers", data)

    if len(packet) == 17:
        # breakdown of "<QffB":
        #   "<": little-endian
        #   "Q": uint64_t (8 bytes)
        #   "f": float (4 bytes)
        #   "B": uint8_t (1 byte)
        ts, lox_celsius, gn2_celsius, _dummy = struct.unpack("<QffB", packet)
        data = {
            "ts": ts,
            "lox_celsius": lox_celsius,
            "gn2_celsius": gn2_celsius,
        }
        return uploader.Record("FsThermocouples", data)


uploader.run(delimiter, parse_packet)
