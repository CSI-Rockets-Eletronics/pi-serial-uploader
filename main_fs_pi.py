import struct
from enum import Enum
from typing import Any

import uploader
from utils import MovingMedianFilter

delimiter = b"\xaa\x55"  # {0b10101010, 0b01010101}


# values must be between 0 and 255 (1 byte)
class FsCommands(Enum):
    STATE_CUSTOM = 0
    STATE_ABORT = 1
    STATE_STANDBY = 2
    STATE_GN2_STANDBY = 3
    STATE_GN2_FILL = 10
    STATE_GN2_PULSE_FILL_A = 11
    STATE_GN2_PULSE_FILL_B = 12
    STATE_GN2_PULSE_FILL_C = 13
    STATE_FIRE = 20
    STATE_FIRE_MANUAL_DOME_PILOT_OPEN = 21
    STATE_FIRE_MANUAL_DOME_PILOT_CLOSE = 22
    STATE_FIRE_MANUAL_IGNITER = 23
    STATE_FIRE_MANUAL_RUN = 24
    RECALIBRATE_TRANSDUCERS = 100
    RESTART = 110


class FsState(Enum):
    CUSTOM = 0
    ABORT = 1
    STANDBY = 2
    GN2_STANDBY = 3
    GN2_FILL = 10
    GN2_PULSE_FILL_A = 11
    GN2_PULSE_FILL_B = 12
    GN2_PULSE_FILL_C = 13
    FIRE = 20
    FIRE_MANUAL_DOME_PILOT_OPEN = 21
    FIRE_MANUAL_DOME_PILOT_CLOSE = 22
    FIRE_MANUAL_IGNITER = 23
    FIRE_MANUAL_RUN = 24


window_size = 30

lox_upper_filter = MovingMedianFilter(window_size)
chamber_filter = MovingMedianFilter(window_size)
gn2_manifold_1_filter = MovingMedianFilter(window_size)
gn2_manifold_2_filter = MovingMedianFilter(window_size)
injector_manifold_1_filter = MovingMedianFilter(window_size)
injector_manifold_2_filter = MovingMedianFilter(window_size)


def parse_packet(packet: bytes):
    # struct FsStatePacket {
    #     FsState state;           // 1 byte
    #     bool gn2_abort;          // 1 byte
    #     bool gn2_fill;           // 1 byte
    #     bool pilot_vent;         // 1 byte
    #     bool dome_pilot_open;    // 1 byte
    #     bool run;                // 1 byte
    #     bool five_two;           // 1 byte
    #     bool water_suppression;  // 1 byte
    #     bool igniter;            // 1 byte
    # };
    if len(packet) == 13:
        # Breakdown of "<IBBBBBBBBB":
        #   "<": little-endian
        #   "I": uint32_t (4 bytes)
        #   "B": uint8_t (1 byte)
        (
            ms_since_boot,
            state,
            gn2_abort,
            gn2_fill,
            pilot_vent,
            dome_pilot_open,
            run,
            five_two,
            water_suppression,
            igniter,
        ) = struct.unpack("<IBBBBBBBBB", packet)
        data = {
            "ms_since_boot": ms_since_boot,
            "state": FsState(state).name,
            "gn2_abort": bool(gn2_abort),
            "gn2_fill": bool(gn2_fill),
            "pilot_vent": bool(pilot_vent),
            "dome_pilot_open": bool(dome_pilot_open),
            "run": bool(run),
            "five_two": bool(five_two),
            "water_suppression": bool(water_suppression),
            "igniter": bool(igniter),
        }
        return uploader.Record("FsState", data)

    if len(packet) == 24:
        # breakdown of "<Qffff":
        #   "<": little-endian
        #   "Q": uint64_t (8 bytes)
        #   "f": float (4 bytes)
        ts, lox_upper, chamber, gn2_manifold_1, gn2_manifold_2 = struct.unpack(
            "<Qffff", packet
        )
        data = {
            "ts": ts,
            "lox_upper": lox_upper,
            "chamber": chamber,
            "gn2_manifold_1": gn2_manifold_1,
            "gn2_manifold_2": gn2_manifold_2,
            "lox_upper_median": lox_upper_filter.add(lox_upper).median(),
            "chamber_median": chamber_filter.add(chamber).median(),
            "gn2_manifold_1_median": gn2_manifold_1_filter.add(gn2_manifold_1).median(),
            "gn2_manifold_2_median": gn2_manifold_2_filter.add(gn2_manifold_2).median(),
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
            "injector_manifold_1_median": injector_manifold_1_filter.add(
                injector_manifold_1
            ).median(),
            "injector_manifold_2_median": injector_manifold_2_filter.add(
                injector_manifold_2
            ).median(),
        }
        return uploader.Record("FsInjectorTransducers", data)

    if len(packet) == 17:
        # breakdown of "<Qfff":
        #   "<": little-endian
        #   "Q": uint64_t (8 bytes)
        #   "f": float (4 bytes)
        ts, lox_celsius, gn2_celsius, gn2_surface_celsius = struct.unpack(
            "<Qfff", packet
        )
        data = {
            "ts": ts,
            "lox_celsius": lox_celsius,
            "gn2_celsius": gn2_celsius,
            "gn2_surface_celsius": gn2_surface_celsius,
        }
        return uploader.Record("FsThermocouples", data)


def format_message(message: Any):
    command = message["command"]
    assert isinstance(command, str)

    try:
        command_value = FsCommands[command].value
    except KeyError:
        raise ValueError(f"Invalid command: {command}")

    # solenoid states
    gn2_abort = False
    gn2_fill = False
    pilot_vent = False
    dome_pilot_open = False
    run = False
    five_two = False
    water_suppression = False
    igniter = False

    if command_value == FsCommands.STATE_CUSTOM.value:
        gn2_abort = message["gn2_abort"]
        gn2_fill = message["gn2_fill"]
        pilot_vent = message["pilot_vent"]
        dome_pilot_open = message["dome_pilot_open"]
        run = message["run"]
        five_two = message["five_two"]
        water_suppression = message["water_suppression"]
        igniter = message["igniter"]

    command_bytes = struct.pack(
        "<BBBBBBBBB",  # 8 bytes
        command_value,
        gn2_abort,
        gn2_fill,
        pilot_vent,
        dome_pilot_open,
        run,
        five_two,
        water_suppression,
        igniter,
    )

    return command_bytes + delimiter


uploader.run(delimiter, parse_packet, {"FiringStation": format_message})
