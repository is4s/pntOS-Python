from time import sleep

from pntos.cobra.mediator import PyMediator
from pntos.cobra.registry import PyRegistry
from pntos.cobra.aspn23_transport_cobra import TransportPlugin as Aspn23Transport
from pntos.cobra.aspn2_transport_cobra import TransportPlugin as Aspn2Transport

def main():
    registry = PyRegistry()
    mediator = PyMediator(registry)

    t23 = Aspn23Transport(None, None)
    t2 = Aspn2Transport(None)

    t23.start_listening()
    t2.start_listening()

    mediator.transport_plugins = [t23, t2]
    t23.mediator = mediator

    sleep(200)

if __name__ == "__main__":
    main()