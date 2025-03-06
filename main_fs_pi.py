import struct
from enum import Enum
from typing import Any

import uploader

delimiter = b"\xaa\x55"  # {0b10101010, 0b01010101}


# values must be between 0 and 255 (1 byte)
class FsCommands(Enum):
    STATE_ABORT = 0
    STATE_STANDBY = 1
    STATE_GN2_STANDBY = 2
    STATE_GN2_FILL = 10
    STATE_GN2_PULSE_FILL_A = 11
    STATE_GN2_PULSE_FILL_B = 12
    STATE_GN2_PULSE_FILL_C = 13
    STATE_FIRE = 20
    STATE_FIRE_MANUAL_DOME_PILOT_OPEN = 21
    STATE_FIRE_MANUAL_DOME_PILOT_CLOSE = 22
    STATE_FIRE_MANUAL_IGNITER = 23
    STATE_FIRE_MANUAL_RUN = 24


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


def format_message(message: Any):
    command = message["command"]
    assert isinstance(command, str)

    try:
        command_value = FsCommands[command].value
    except KeyError:
        raise ValueError(f"Invalid command: {command}")

    return struct.pack("<B", command_value) + delimiter


uploader.run(delimiter, parse_packet, {"FiringStation": format_message})
