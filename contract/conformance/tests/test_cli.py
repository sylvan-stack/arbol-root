# Compatibility entry: the mid-tier implementation lives in tests/mid/archived/contract/conformance/tests/test_cli.py.
# Keep the original module/package and __file__ so existing fixtures resolve unchanged.
from pathlib import Path as _TierPath
_tier_source = _TierPath(__file__).resolve().parents[3] / 'tests/mid/archived/contract/conformance/tests/test_cli.py'
exec(compile(_tier_source.read_bytes(), str(_tier_source), "exec"), globals())

# LOW TIER — DO NOT ENABLE OR RECREATE
# Historical examples only. Read before adding related tests; never execute.
# LOW-TIER-BEGIN: contract/conformance/tests/test_cli.py::Cli.test_help
# Reason: Only checks the fixed help branch returns zero and includes a declared option; the actual parser/refusal/runner boundaries are exercised elsewhere.
# Source: arbol-root@e9170eed1ea69b5b5c3b7a140657583e52e2f8b4:contract/conformance/tests/test_cli.py
# Retained evidence at review: CLI argument refusal, selection, complete execution and error-reporting cases remain.
# Historical fixtures and class context are available at the source revision; no active dependencies restored.
# LOW-TIER-SOURCE-BEGIN
#     def test_help(self) -> None:
#         result = suite("--help")
#         self.assertEqual(result.returncode, 0)
#         self.assertIn("--root-contract", result.stdout)
# LOW-TIER-SOURCE-END
# LOW-TIER-END
