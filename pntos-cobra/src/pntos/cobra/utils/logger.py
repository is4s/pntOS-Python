#!/usr/bin/env python3

import argparse
from threading import Thread
from time import time

from lcm import LCM, EventLog


class Logger:
    output_log: EventLog

    def __init__(self, output_log_path: str) -> None:
        self.output_log = EventLog(output_log_path, 'w', overwrite=True)

    def __del__(self) -> None:
        self.output_log.close()

    def general_handler(self, channel: str, data: bytes) -> None:
        time_microsec = int(time() * 1e6)
        self.output_log.write_event(time_microsec, channel, data)


def handler_thread(lcm: LCM) -> None:
    """Call LCM.handle in a loop."""
    while True:
        # Wait 5s before giving up on additional messages coming in
        if lcm.handle_timeout(5000):
            continue
        print('Timed out, shutting down logger')
        break


def main(output_log_path: str) -> None:
    try:
        lcm = LCM('tcpq://')
    except RuntimeError as e:
        print(f'Failed to start lcm: {e}')
        return
    logger = Logger(output_log_path)
    lcm.subscribe(r'.*', logger.general_handler)

    handler = Thread(target=handler_thread, args=[lcm])
    handler.start()
    handler.join()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Logs LCM network traffic to a file')
    parser.add_argument('output_log_path', help='Path to output file', type=str)
    args = parser.parse_args()
    main(args.output_log_path)
