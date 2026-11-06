#!/usr/bin/env python3
"""PWGen · DGKN@Labs

Launcher retained for backwards compatibility with earlier releases.
The application itself lives in the ``dgknlabs`` package.
"""

import sys

from dgknlabs.app import main

if __name__ == "__main__":
    sys.exit(main())
