import sys

RED = '\033[91m'
GREEN = '\033[92m'
BLUE = '\033[94m'

try:
    from pntos.api import ControllerPlugin
    from pntos.cobra import StandardControllerPlugin
except ModuleNotFoundError:
    print(f'{RED}ERROR: Installation failed!\033[0m')
    print(
        f"See '{BLUE}https://pntos.pages.aspn.us/pntos-python/installation.html#errata-troubleshooting\033[0m' for troubleshooting steps."
    )
    sys.exit(1)

print(f'{GREEN}Installation successful!\033[0m')
