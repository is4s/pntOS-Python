from time import sleep

from pntos.cobra.Aspn2LCMTransportPlugin import TransportPlugin as Aspn2Transport
from pntos.cobra.Aspn23LCMTransportPlugin import TransportPlugin as Aspn23Transport
from pntos.cobra.mediator import PyMediator
from pntos.cobra.registry import PyRegistry


def main():
    registry = PyRegistry()
    mediator = PyMediator(registry)

    t23 = Aspn23Transport(mediator)
    t2 = Aspn2Transport(mediator)

    t23.start_listening()
    t2.start_listening()

    mediator.transport_plugins = [t23, t2]
    t23.mediator = mediator

    sleep(200)


if __name__ == "__main__":
    main()
