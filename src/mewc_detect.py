"""Alternate entrypoint sharing the same validated runner."""
import sys
from mewc_runner import main

if __name__ == '__main__':
    sys.exit(main())
