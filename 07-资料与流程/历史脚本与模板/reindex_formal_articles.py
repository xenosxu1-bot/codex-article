# -*- coding: utf-8 -*-
"""Deprecated safeguard for formal-article renumbering.

Formal article IDs must not be renumbered during routine retirement.  A one-time
migration requires an explicitly approved mapping in
07-?????/??????.md and a separately reviewed implementation batch.
"""
from __future__ import annotations
import sys


def main() -> int:
    print('Blocked: routine automatic formal-article renumbering is disabled.')
    print('Create and approve a mapping in 07-?????/??????.md first, then run the documented migration checks.')
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
