import os

import tbot.tbot


if __name__ == '__main__':
    if os.name == 'nt':
        os.environ.setdefault('DEBUG', str(True))
    tbot.tbot.run()
