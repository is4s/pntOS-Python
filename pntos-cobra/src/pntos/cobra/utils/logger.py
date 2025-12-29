#!/usr/bin/env python3

import argparse
from threading import Thread
from time import time

from lcm import LCM, EventLog


class Logger:
    output_log: EventLog
    desired_num_events: int | None
    channel_to_count: str | None
    num_events: int

    def __init__(
        self,
        output_log_path: str,
        desired_num_events: int | None,
        channel_to_count: str | None,
    ) -> None:
        self.output_log = EventLog(output_log_path, 'w', overwrite=True)
        self.desired_num_events = desired_num_events
        self.channel_to_count = channel_to_count
        self.num_events = 0

    def __del__(self) -> None:
        self.output_log.close()

    def general_handler(self, channel: str, data: bytes) -> None:
        if self.channel_to_count is not None and channel == self.channel_to_count:
            self.num_events += 1
        time_microsec = int(time() * 1e6)
        self.output_log.write_event(time_microsec, channel, data)

    def handler_thread(self, lcm: LCM) -> None:
        """Call LCM.handle in a loop."""
        while True:
            # Wait 60s before giving up on additional messages coming in
            if lcm.handle_timeout(60000):
                if (
                    self.desired_num_events is not None
                    and self.num_events >= self.desired_num_events
                ):
                    print('Number of target events reached, shutting down logger')
                    break
                continue
            print('Timed out, shutting down logger')
            break


def main(
    output_log_path: str, desired_num_events: int | None, channel_to_count: str | None
) -> None:
    try:
        lcm = LCM('tcpq://')
    except RuntimeError as e:
        print(f'Failed to start lcm: {e}')
        return
    logger = Logger(output_log_path, desired_num_events, channel_to_count)
    lcm.subscribe(r'.*', logger.general_handler)

    handler = Thread(target=logger.handler_thread, args=[lcm])
    handler.start()
    handler.join()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Logs LCM network traffic to a file')
    parser.add_argument('output_log_path', help='Path to output file', type=str)
    parser.add_argument(
        'desired_num_events',
        help='Number of events to count before shutting down',
        type=int,
        default=None,
    )
    parser.add_argument(
        'channel_to_count',
        help='Channel to look for events before shutting down',
        type=str,
        default=None,
    )
    args = parser.parse_args()
    main(args.output_log_path, args.desired_num_events, args.channel_to_count)
