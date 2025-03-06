import struct

import uploader

delimiter = b"\xaa\x55"  # {0b10101010, 0b01010101}


def parse_packet(packet: bytes):
    if len(packet) == 20:
        # breakdown of "!qhhhhhh":
        #   "!": network byte order
        #   "q": long long
        #   "h": short
        ts, ax, ay, az, gx, gy, gz = struct.unpack("!qhhhhhh", packet)
        data = {"ts": ts, "ax": ax, "ay": ay, "az": az, "gx": gx, "gy": gy, "gz": gz}
        return uploader.Record("MPU", data)

    if len(packet) == 16:
        # breakdown of "!qff":
        #   "!": network byte order
        #   "q": long long
        #   "f": float
        ts, temp, hum = struct.unpack("!qff", packet)
        data = {"ts": ts, "temp": temp, "hum": hum}
        return uploader.Record("DHT", data)


uploader.run(delimiter, parse_packet)
