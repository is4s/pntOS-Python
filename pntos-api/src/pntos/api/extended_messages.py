"""Python API of pntOS."""

from dataclasses import dataclass

from aspn23 import AspnBase


@dataclass
class MarkerMessage(AspnBase):
    """
    A heartbeat message containing a timestamp.

    One example use-case of this message is when a
    filter should be propagated to a certain time but no filter update needs to be performed.

    Attributes:
        elapsed_nsec (int): Whole number of nanoseconds elapsed since the ASPN system time epoch.
            If negative, whole number nanoseconds until the ASPN system time epoch.
    """

    elapsed_nsec: int


@dataclass
class SerializedMessage(AspnBase):
    """
    An extended ASPN message for serialized data.

    Serialized data with an identifier that can be used for message routing through the pntOS system.
    The serialized data can be used for communication between plugins where only the sending and
    receiving plugins need to know how to encode or decode the message.

    Attributes:
        elapsed_nsec (int): Whole number of nanoseconds elapsed since timestamp's zero epoch.
            If negative, whole number nanoseconds until timestamp's zero epoch.

        identifier (str): A unique identifier for this serialized message.

        data (bytes): A pointer to a serialized data stream. The data stream format can be based on
            the content of the above identifier. Two plugins communicating by sharing this data must
            agree on a format, such that they both interpret the data the same way.
    """

    elapsed_nsec: int
    identifier: str
    data: bytes
