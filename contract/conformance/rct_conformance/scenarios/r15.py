# Compatibility entry: the mid-tier implementation lives in tests/mid/archived/contract/conformance/rct_conformance/scenarios/r15.py.
# Keep the original module/package and __file__ so existing fixtures resolve unchanged.
from pathlib import Path as _TierPath
_tier_source = _TierPath(__file__).resolve().parents[4] / 'tests/mid/archived/contract/conformance/rct_conformance/scenarios/r15.py'
exec(compile(_tier_source.read_bytes(), str(_tier_source), "exec"), globals())
