import uploader
import struct
import json

delimiter = b"\xAA\x55"  # {0b10101010, 0b01010101}


def parse_device(packet: bytes) -> str:
    if len(packet) == 23:
        return "GPS"
    if len(packet) == 20:
        return "IMU"
    if len(packet) == 16:
        return "DHT"
    raise ValueError(f"Invalid packet length: {len(packet)}")


def parse_packet(packet: bytes) -> str:
    if len(packet) == 23:
        # breakdown of "<QBBBiif":
        #   "<": little-endian
        #   "Q": uint64_t (8 bytes)
        #   "B": uint8_t (1 byte)
        #   "B": uint8_t (1 byte)
        #   "B": uint8_t (1 byte)
        #   "i": int32_t (4 bytes)
        #   "i": int32_t (4 bytes)
        #   "f": float (4 bytes)
        (
            ts,
            fix,
            fixquality,
            satellites,
            latitude_fixed,
            longitude_fixed,
            altitude,
        ) = struct.unpack("<QBBBiif", packet)
        data = {
            "ts": ts,
            "fix": fix,
            "fixquality": fixquality,
            "satellites": satellites,
            "latitude_fixed": latitude_fixed,
            "longitude_fixed": longitude_fixed,
            "altitude": altitude,
        }
        return json.dumps(data)

    if len(packet) == 20:
        # breakdown of "<QHHHHHH":
        #   "<": little-endian
        #   "Q": uint64_t (8 bytes)
        #   "h": int16_t (2 bytes)
        #   "h": int16_t (2 bytes)
        #   "h": int16_t (2 bytes)
        #   "h": int16_t (2 bytes)
        #   "h": int16_t (2 bytes)
        #   "h": int16_t (2 bytes)
        ts, ax, ay, az, gx, gy, gz = struct.unpack("<Qhhhhhh", packet)
        data = {
            "ts": ts,
            "ax": ax,
            "ay": ay,
            "az": az,
            "gx": gx,
            "gy": gy,
            "gz": gz,
        }
        return json.dumps(data)

    if len(packet) == 16:
        # breakdown of "<Qff":
        #   "<": little-endian
        #   "Q": uint64_t (8 bytes)
        #   "f": float (4 bytes)
        #   "f": float (4 bytes)
        ts, temperature, humidity = struct.unpack("<Qff", packet)
        data = {
            "ts": ts,
            "temperature": temperature,
            "humidity": humidity,
        }
        return json.dumps(data)

    raise ValueError(f"Invalid packet length: {len(packet)}")


uploader.run(parse_device, delimiter, parse_packet)
