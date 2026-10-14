"""``python -m pflog``."""

from __future__ import annotations

import sys

from pflog.cli.commands import main

if __name__ == "__main__":
    sys.exit(main())
