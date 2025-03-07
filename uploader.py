import sys
import time
from dataclasses import dataclass
from threading import Thread
from typing import Any, Callable

import requests
import serial

MAX_RECORDS_PER_BATCH = 500

URL = "http://localhost:3000"
ENVIRONMENT_KEY = "0"

ser = serial.Serial("/dev/ttyS0", 230400)


@dataclass
class Record:
    device: str
    data: dict[str, Any]
    """JSON-serializable data"""


PacketParser = Callable[[bytes], Record | None]
MessageFormatter = Callable[[Any], bytes]


def fetch_ts():
    result = requests.get(
        f"{URL}/ts",
        headers={"content-type": "application/json"},
    )

    if result.status_code != 200:
        raise Exception(f"Error fetching ts from server (status: {result.status_code})")

    return result.json()


last_ts = fetch_ts()


def post_records(device: str, records: list[Any]):
    body = {
        "environmentKey": ENVIRONMENT_KEY,
        "device": device,
        "records": records,
    }

    try:
        result = requests.post(
            f"{URL}/records/batch",
            # no compression
            json=body,
            headers={"content-type": "application/json"},
        )
    except Exception as e:
        if isinstance(e, KeyboardInterrupt):
            sys.exit(0)

        print(
            f"Error sending records to server (requests.post failed)",
            file=sys.stderr,
        )
        return

    if result.status_code != 200:
        print(
            f"Error sending records to server (status: {result.status_code})",
            file=sys.stderr,
        )
    else:
        print(
            f"Sent {len(records)} records to server for device {device}",
            file=sys.stderr,
        )


def get_message(device: str) -> Any | None:
    global last_ts

    params = {
        "environmentKey": ENVIRONMENT_KEY,
        "device": device,
        "afterTs": last_ts,
    }

    try:
        result = requests.get(
            f"{URL}/messages/next",
            params=params,
            headers={"content-type": "application/json"},
        )
    except Exception as e:
        if isinstance(e, KeyboardInterrupt):
            sys.exit(0)

        print(
            "Error reading message from server (requests.get failed)",
            file=sys.stderr,
        )
        return None

    if result.status_code != 200:
        print(
            f"Error reading message from server (status: {result.status_code})",
            file=sys.stderr,
        )
        return None
    elif result.text == "NONE":
        return None
    else:
        body = result.json()
        if "ts" not in body:
            print("Messages response is missing ts field", file=sys.stderr)
            return None
        if "data" not in body:
            print("Messages response is missing data field", file=sys.stderr)
            return None

        last_ts = body["ts"]

        return body["data"]


def run_poll_messages(device: str, format_message: MessageFormatter):
    while True:
        message = get_message(device)
        if message is not None:
            print(f"Received message from server: {message}", file=sys.stderr)

            try:
                message = format_message(message)
            except Exception as e:
                print(
                    "Error formatting message:",
                    e,
                    file=sys.stderr,
                )
                continue

            ser.write(message)


def run(
    delimiter: bytes,
    parse_packet: PacketParser,
    message_formatters: dict[str, MessageFormatter] = {},
):
    """
    Continuously read from serial port and send data to server.

    delimiter: delimiter between serial packets
    parse_packet: function to parse a serial packet into a device + json data; return None to skip the packet.
    message_formatters: map of device names (to poll) to functions that convert a message object into bytes to send to the serial port
    """

    # throw away possibly partial packet
    ser.read_until(delimiter)

    for device, format_message in message_formatters.items():
        Thread(target=run_poll_messages, args=(device, format_message)).start()

    post_thread: Thread | None = None

    while True:
        # device -> records
        records_dict: dict[str, list[Any]] = {}
        records_count = 0

        while (
            len(records_dict) == 0  # loop until >= 1 record is read
            or ser.in_waiting > 0  # loop until no more data is available
            # loop until the last batch is posted
            or (post_thread and post_thread.is_alive())
        ):
            input_packet = ser.read_until(delimiter)
            # remove delimiter
            input_packet = input_packet[: -len(delimiter)]

            try:
                record = parse_packet(input_packet)
            except Exception as e:
                print(
                    "Error parsing input packet:",
                    e,
                    file=sys.stderr,
                )
                continue

            if record is None:
                print(f"Skipping packet of length {len(input_packet)}", file=sys.stderr)
                continue

            if records_count >= MAX_RECORDS_PER_BATCH:
                continue

            if record.device not in records_dict:
                records_dict[record.device] = []

            records_dict[record.device].append(
                {
                    "ts": time.time_ns() // 1000,
                    "data": record.data,
                }
            )
            records_count += 1

        for device, records in records_dict.items():
            post_thread = Thread(target=post_records, args=(device, records))
            post_thread.start()
