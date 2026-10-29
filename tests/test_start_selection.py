# Shared fixtures; case bodies live in top/ and mid/. See TESTS.md.
from __future__ import annotations
import copy
from unittest import mock


import sys
import unittest
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from arbol_root.input import FORWARD, parse  # noqa: E402
from arbol_root.launcher import Reply, select_build  # noqa: E402
from arbol_root.model import Identity, Refusal  # noqa: E402

from arbol_root.model import Identity  # noqa: E402

EXCHANGE = '7f3a2c1e-4b5d-4e6f-8a9b-0c1d2e3f4a5b'
BASE = ['start','--exchange',EXCHANGE,'--request','request.json']
INVENTORY: dict[str, Any] = {'root':'sapling','rootContract':1,'trunks':[{'trunk':'trivial','builds':[
    {'build':'a','status':'working','fits':True,'runnable':True,'chosen':True},
    {'build':'9','status':'withdrawn','fits':True,'runnable':True,'chosen':False},
    {'build':'8','status':'working','fits':False,'runnable':True,'chosen':False}]}]}


class Selection(unittest.TestCase):
    context = Identity('sapling','0','1.0.0',Path('/private-fixture/root'),Path('/private-fixture/bin'))


# Archived complete imports; restore needed names in their original scope, not at this file tail.
