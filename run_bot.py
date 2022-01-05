import os

import tbot.tbot


def run_bot() -> None:
    tbot.tbot.run()


if __name__ == '__main__':
    if os.name == 'nt':
        os.environ.setdefault('DEBUG', str(True))
    run_bot()
