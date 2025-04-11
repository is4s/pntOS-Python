#!/usr/bin/env python3

from aspn23_lcm import measurement_IMU, measurement_position_velocity_attitude
from lcm import EventLog

PARSERS = {
    'imu': measurement_IMU,
    'positionvelocityattitude': measurement_position_velocity_attitude,
}


class LcmDataHelper:
    def __init__(self, decode_class_name, decode_class):
        self.lcm_type = 'Unknown'
        self.decode_class_name = decode_class_name
        self.decode_class = decode_class
        self.data = []


def validate_requested(requested, allowed):
    to_remove = []
    for item in requested:
        if allowed.count(item) == 0:
            print('No datatype matching {} found, ignoring'.format(item))
            to_remove.append(item)
    for item in to_remove:
        requested.remove(item)


def strip_empties(mp):
    to_remove = []
    for item in mp.items():
        if len(item[1].data) == 0:
            to_remove.append(item[0])
    for key in to_remove:
        mp.pop(key)


def get_converter(data):
    for opt in PARSERS.items():
        try:
            opt[1].decode(data)
            return opt
        except:
            pass
    return None


def harvest(argpth, types_to_view):
    mp = dict()
    lg = EventLog(argpth)

    validate_requested(types_to_view, list(PARSERS))
    if len(types_to_view) == 0:
        print('No valid data types supplied. Exiting.')
        return

    for ev in lg:
        if ev.channel not in mp:
            converter = get_converter(ev.data)
            if converter:
                mp[ev.channel] = LcmDataHelper(converter[0], converter[1])
            else:
                print('No parser for channel{}'.format(ev.channel))
                mp[ev.channel] = LcmDataHelper('', None)
        if (
            mp[ev.channel].decode_class_name in types_to_view
            and mp[ev.channel].decode_class
        ):
            msg = mp[ev.channel].decode_class.decode(ev.data)
            mp[ev.channel].data.append(msg)
    strip_empties(mp)
    return mp


def harvest_by_channel(argpth, channels):
    mp = dict()
    lg = EventLog(argpth)

    for ev in lg:
        if ev.channel in channels:
            if ev.channel not in mp:
                converter = get_converter(ev.data)
                if converter:
                    mp[ev.channel] = LcmDataHelper(converter[0], converter[1])
                else:
                    print('No parser for channel{}'.format(ev.channel))
                    mp[ev.channel] = LcmDataHelper('', None)
            if mp[ev.channel].decode_class:
                msg = mp[ev.channel].decode_class.decode(ev.data)
                mp[ev.channel].data.append(msg)
    strip_empties(mp)
    return mp


def report_available_channels(argpth):
    mp = dict()
    lg = EventLog(argpth)

    for ev in lg:
        if ev.channel not in mp:
            converter = get_converter(ev.data)
            if converter:
                mp[ev.channel] = converter[0]
            else:
                mp[ev.channel] = 'Unknown'

    print('Channels and data types in {}'.format(argpth))
    for found in mp.items():
        print('{} : {}'.format(found[0], found[1]))
