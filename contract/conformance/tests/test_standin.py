# Compatibility entry: the mid-tier implementation lives in tests/mid/archived/contract/conformance/tests/test_standin.py.
# Keep the original module/package and __file__ so existing fixtures resolve unchanged.
from pathlib import Path as _TierPath
_tier_source = _TierPath(__file__).resolve().parents[3] / 'tests/mid/archived/contract/conformance/tests/test_standin.py'
exec(compile(_tier_source.read_bytes(), str(_tier_source), "exec"), globals())

# LOW TIER — DO NOT ENABLE OR RECREATE
# Historical examples only. Read before adding related tests; never execute.
# LOW-TIER-BEGIN: contract/conformance/tests/test_standin.py::StandIn.test_info_names_contract_1_and_the_build
# Reason: Tests static metadata of the test stand-in, echoing its selected fake build and launcher name.
# Source: arbol-root@461501ecd9ab475444aefc8b063db9cb97c18c27:contract/conformance/tests/test_standin.py
# Retained evidence at review: Actual product identity and stand-in protocol/process lifecycle checks remain.
# Historical fixtures and class context are available at the source revision; no active dependencies restored.
# LOW-TIER-SOURCE-BEGIN
#     def test_info_names_contract_1_and_the_build(self) -> None:
#         """standin.info: `-v <build> info` names the Driver of the launcher, the build and contract 1."""
#         process = self.start(["-v", "7", "info"], launcher="arbol-codex-driver")
#         output, _ = process.communicate(timeout=30)
#         info = json.loads(output)
#         self.assertEqual((info["driver"], info["build"], info["contract"]), ("codex", "7", 1))
#         self.assertEqual(self.received()[0]["arguments"], ["-v", "7", "info"])
#         self.assertEqual(self.received()[0]["launcher"], "arbol-codex-driver")
# LOW-TIER-SOURCE-END
# LOW-TIER-END

# LOW-TIER-BEGIN: contract/conformance/tests/test_standin.py::StandIn.test_capabilities_offer_the_selected_subscription_without_a_run
# Reason: Copies two hard-coded family/subscription lists returned by the stand-in; no production capability behavior is exercised.
# Source: arbol-root@461501ecd9ab475444aefc8b063db9cb97c18c27:contract/conformance/tests/test_standin.py
# Retained evidence at review: Actual driver capability/account tests and substantive conformance scenarios remain.
# Historical fixtures and class context are available at the source revision; no active dependencies restored.
# LOW-TIER-SOURCE-BEGIN
#     def test_capabilities_offer_the_selected_subscription_without_a_run(self) -> None:
#         for command, expected in (
#             (["subscriptions", "families"], [{"id": "anthropic", "auth": "vendor_login"}]),
#             (["subscriptions", "list"], [{"id": "standin", "family": "anthropic"},
#                                         {"id": "anthropic", "family": "anthropic"}]),
#         ):
#             process = self.start(command)
#             output, _ = process.communicate(timeout=30)
#             self.assertEqual(process.returncode, 0)
#             self.assertEqual(json.loads(output), expected)
# LOW-TIER-SOURCE-END
# LOW-TIER-END
