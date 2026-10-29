
# LOW TIER — DO NOT ENABLE OR RECREATE
# Historical examples only. Read before adding related tests; never execute.
# LOW-TIER-BEGIN: tests/mid/test_mid_settle.py::Settling.test_named_settle_delegates_missing_or_living_exchange_to_exact_chosen_build
# Reason: Mocked return-state mappings, simple refusal predicates and normal delegation add no distinct evidence beyond actual concurrent shared settling/recovery. Case reviewed: root.settle-named
# Source: arbol-root@ef4fd6a30eca7130653b20e5eedf0da7be72aaa4:tests/mid/test_mid_settle.py
# Historical fixtures and class context are available at the source revision; no active dependencies restored.
# LOW-TIER-SOURCE-BEGIN
#     def test_named_settle_delegates_missing_or_living_exchange_to_exact_chosen_build(self) -> None:
#         """root.settle-named"""
#         name = record(1)['exchange']
#         answer = self.f.cli('settle', name)
#         self.assertEqual(answer.returncode, 0, answer.stderr)
#         self.assertEqual(json.loads(answer.stdout), {'root':'sapling', 'results':[
#             {'exchange':name, 'settled':'interrupted'}]})
#         self.assertEqual([c['args'] for c in self.f.calls()], [
#             ['--root','sapling','trivial','list'], ['--root','sapling','trivial','-v','a','settle',name]])
#         self.f.put(record(1))
#         self.f.script(settled=None, stdout='{"error":{"code":"alive","message":"still living"}}\n')
#         result = settle(self.f.context, name)
#         self.assertEqual(result.status, 1)
#         self.assertEqual(result.value['results'][0]['exchange'], name)
#         self.assertEqual(result.value['results'][0]['error']['code'], 'alive')
# LOW-TIER-SOURCE-END
# LOW-TIER-END

# LOW-TIER-BEGIN: tests/mid/test_mid_settle.py::Settling.test_all_settle_is_lexical_skips_living_and_selects_only_once
# Reason: Mocked return-state mappings, simple refusal predicates and normal delegation add no distinct evidence beyond actual concurrent shared settling/recovery. Case reviewed: root.settle-all
# Source: arbol-root@ef4fd6a30eca7130653b20e5eedf0da7be72aaa4:tests/mid/test_mid_settle.py
# Historical fixtures and class context are available at the source revision; no active dependencies restored.
# LOW-TIER-SOURCE-BEGIN
#     def test_all_settle_is_lexical_skips_living_and_selects_only_once(self) -> None:
#         """root.settle-all"""
#         for i in [3, 2, 1]:
#             folder = self.f.put(record(i, pid=123 if i == 2 else 456, accepted=i != 1, ended=i == 3))
#             (folder / 'events.jsonl').write_bytes(b'not read by the manager')
#         def actual(pid: int) -> datetime | None:
#             return datetime(2026,10,26,9,tzinfo=UTC) if pid == 123 else None
#         with mock.patch('arbol_root.process.started_at', side_effect=actual):
#             reply = settle(self.f.context)
#         self.assertEqual([v['exchange'] for v in reply.value['results']], [record(1)['exchange'],record(3)['exchange']])
#         self.assertEqual(reply.status, 0)
#         self.assertEqual(len(self.f.calls()), 3)
#         self.assertEqual(self.f.calls()[0]['args'], ['--root','sapling','trivial','list'])
# LOW-TIER-SOURCE-END
# LOW-TIER-END

# LOW-TIER-BEGIN: tests/mid/test_mid_settle.py::Settling.test_empty_or_only_living_needs_no_launcher
# Reason: Mocked return-state mappings, simple refusal predicates and normal delegation add no distinct evidence beyond actual concurrent shared settling/recovery. Case reviewed: root.settle-empty
# Source: arbol-root@ef4fd6a30eca7130653b20e5eedf0da7be72aaa4:tests/mid/test_mid_settle.py
# Historical fixtures and class context are available at the source revision; no active dependencies restored.
# LOW-TIER-SOURCE-BEGIN
#     def test_empty_or_only_living_needs_no_launcher(self) -> None:
#         """root.settle-empty"""
#         (self.f.bin / 'arbol-trunk').unlink()
#         self.assertEqual(settle(self.f.context).value, {'root':'sapling','results':[]})
#         self.f.put(record(1))
#         with mock.patch('arbol_root.process.started_at', return_value=datetime(2026,10,26,9,tzinfo=UTC)):
#             self.assertEqual(settle(self.f.context).status, 0)
#         self.assertEqual(self.f.calls(), [])
# LOW-TIER-SOURCE-END
# LOW-TIER-END

# LOW-TIER-BEGIN: tests/mid/test_mid_settle.py::Settling.test_database_refusal_stops_before_the_next_exchange_and_keeps_extra_fields
# Reason: Mocked return-state mappings, simple refusal predicates and normal delegation add no distinct evidence beyond actual concurrent shared settling/recovery. Case reviewed: root.settle-database-refusal
# Source: arbol-root@ef4fd6a30eca7130653b20e5eedf0da7be72aaa4:tests/mid/test_mid_settle.py
# Historical fixtures and class context are available at the source revision; no active dependencies restored.
# LOW-TIER-SOURCE-BEGIN
#     def test_database_refusal_stops_before_the_next_exchange_and_keeps_extra_fields(self) -> None:
#         """root.settle-database-refusal"""
#         for i in [1, 2, 3]:
#             self.f.put(record(i))
#         name = record(2)['exchange']
#         refusal = {'error':{'code':'database_unavailable','message':'offline'}, 'extra':{'retry':True}}
#         self.f.script(outcomes={name:{'stdout':json.dumps(refusal)+'\n'}})
#         script = json.loads((self.f.bin / 'script.json').read_text())
#         script['responses']['settle']['stdout'] = '{"settled":"completed"}\n'
#         (self.f.bin / 'script.json').write_text(json.dumps(script))
#         with mock.patch('arbol_root.process.started_at', return_value=None):
#             reply = settle(self.f.context)
#         self.assertEqual(reply.status, 1)
#         self.assertEqual(len(self.f.calls()), 3)
#         self.assertEqual(reply.value['results'][-1], {'exchange':name, **refusal})
# LOW-TIER-SOURCE-END
# LOW-TIER-END

# LOW-TIER-BEGIN: tests/mid/test_mid_settle.py::Settling.test_no_fit_and_selection_refusal_never_start_settling
# Reason: Mocked return-state mappings, simple refusal predicates and normal delegation add no distinct evidence beyond actual concurrent shared settling/recovery. Case reviewed: root.settle-selection
# Source: arbol-root@ef4fd6a30eca7130653b20e5eedf0da7be72aaa4:tests/mid/test_mid_settle.py
# Historical fixtures and class context are available at the source revision; no active dependencies restored.
# LOW-TIER-SOURCE-BEGIN
#     def test_no_fit_and_selection_refusal_never_start_settling(self) -> None:
#         """root.settle-selection"""
#         value = copy.deepcopy(INVENTORY)
#         value['trunks'][0]['builds'][0]['chosen'] = False
#         with mock.patch('arbol_root.launcher.list_reply', return_value=Reply(b'{}',value,0)):
#             with self.assertRaises(Refusal) as error:
#                 settle(self.f.context, record(1)['exchange'])
#         self.assertEqual((error.exception.code,error.exception.available), ('no_fit',['a']))
#         refused = Reply(b' {"error":{"code":"no_fit"},"available":[]}\n', {'error':{'code':'no_fit'}}, 1)
#         with mock.patch('arbol_root.settle.chosen_build', return_value=refused):
#             self.assertIs(settle(self.f.context, record(1)['exchange']), refused)
#         self.assertEqual(self.f.calls(), [])
# LOW-TIER-SOURCE-END
# LOW-TIER-END

# LOW-TIER-BEGIN: tests/mid/test_mid_settle.py::Settling.test_missing_or_nonobject_settle_reply_is_a_per_exchange_refusal
# Reason: Mocked return-state mappings, simple refusal predicates and normal delegation add no distinct evidence beyond actual concurrent shared settling/recovery. Case reviewed: root.settle-unavailable
# Source: arbol-root@ef4fd6a30eca7130653b20e5eedf0da7be72aaa4:tests/mid/test_mid_settle.py
# Historical fixtures and class context are available at the source revision; no active dependencies restored.
# LOW-TIER-SOURCE-BEGIN
#     def test_missing_or_nonobject_settle_reply_is_a_per_exchange_refusal(self) -> None:
#         """root.settle-unavailable"""
#         name = record(1)['exchange']
#         for stdout in ['', '[]\nnot-json\n']:
#             self.f.script(stdout=stdout)
#             with mock.patch('arbol_root.settle.chosen_build', return_value='a'):
#                 reply = settle(self.f.context, name)
#             self.assertEqual(reply.value['results'][0]['error']['code'], 'trunk_unavailable')
#             self.assertEqual(reply.status, 1)
#         (self.f.bin / 'arbol-trunk').unlink()
#         with mock.patch('arbol_root.settle.chosen_build', return_value='a'):
#             self.assertEqual(settle_after_stop(self.f.context, name)['error']['code'], 'trunk_unavailable')
# LOW-TIER-SOURCE-END
# LOW-TIER-END

# LOW-TIER-BEGIN: tests/mid/test_mid_settle.py::Settling.test_unreadable_record_is_retained_and_reported_without_delegation
# Reason: Mocked return-state mappings, simple refusal predicates and normal delegation add no distinct evidence beyond actual concurrent shared settling/recovery. Case reviewed: root.settle-unreadable
# Source: arbol-root@ef4fd6a30eca7130653b20e5eedf0da7be72aaa4:tests/mid/test_mid_settle.py
# Historical fixtures and class context are available at the source revision; no active dependencies restored.
# LOW-TIER-SOURCE-BEGIN
#     def test_unreadable_record_is_retained_and_reported_without_delegation(self) -> None:
#         """root.settle-unreadable"""
#         folder = self.f.put(record(1))
#         (folder / 'record.json').write_text('{bad}')
#         reply = settle(self.f.context)
#         self.assertEqual(reply.status, 1)
#         self.assertEqual(reply.value['results'][0]['error']['code'], 'root_unavailable')
#         self.assertTrue(folder.is_dir())
#         self.assertEqual(self.f.calls(), [])
# LOW-TIER-SOURCE-END
# LOW-TIER-END

# LOW-TIER-BEGIN: tests/mid/test_mid_settle.py::Settling.test_stop_gets_a_selection_failure_as_an_outcome
# Reason: Mocked return-state mappings, simple refusal predicates and normal delegation add no distinct evidence beyond actual concurrent shared settling/recovery. Case reviewed: Stop gets a selection failure as an outcome.
# Source: arbol-root@ef4fd6a30eca7130653b20e5eedf0da7be72aaa4:tests/mid/test_mid_settle.py
# Historical fixtures and class context are available at the source revision; no active dependencies restored.
# LOW-TIER-SOURCE-BEGIN
#     def test_stop_gets_a_selection_failure_as_an_outcome(self) -> None:
#         with mock.patch('arbol_root.settle.chosen_build', side_effect=Refusal('no_fit','none',['b'])):
#             value = settle_after_stop(self.f.context, record(1)['exchange'])
#         self.assertEqual(value['error']['code'], 'no_fit')
#         self.assertEqual(value['available'], ['b'])
# LOW-TIER-SOURCE-END
# LOW-TIER-END

# LOW-TIER-BEGIN: tests/mid/test_mid_settle.py::Settling.test_nonzero_child_status_is_not_reported_as_success
# Reason: Mocked return-state mappings, simple refusal predicates and normal delegation add no distinct evidence beyond actual concurrent shared settling/recovery. Case reviewed: root.settle-child-status
# Source: arbol-root@ef4fd6a30eca7130653b20e5eedf0da7be72aaa4:tests/mid/test_mid_settle.py
# Historical fixtures and class context are available at the source revision; no active dependencies restored.
# LOW-TIER-SOURCE-BEGIN
#     def test_nonzero_child_status_is_not_reported_as_success(self) -> None:
#         """root.settle-child-status"""
#         self.f.script(stdout='diagnostic\n{"settled":"completed","extra":3}\n', status=7)
#         reply = settle(self.f.context, record(1)['exchange'])
#         self.assertEqual(reply.status, 1)
#         self.assertEqual(reply.value['results'][0]['extra'], 3)
# LOW-TIER-SOURCE-END
# LOW-TIER-END

# LOW-TIER-BEGIN: tests/mid/test_mid_settle.py::Settling.test_success_without_a_state_or_with_a_different_exchange_is_unavailable
# Reason: Mocked return-state mappings, simple refusal predicates and normal delegation add no distinct evidence beyond actual concurrent shared settling/recovery. Case reviewed: root.settle-reply-identity
# Source: arbol-root@ef4fd6a30eca7130653b20e5eedf0da7be72aaa4:tests/mid/test_mid_settle.py
# Historical fixtures and class context are available at the source revision; no active dependencies restored.
# LOW-TIER-SOURCE-BEGIN
#     def test_success_without_a_state_or_with_a_different_exchange_is_unavailable(self) -> None:
#         """root.settle-reply-identity"""
#         name = record(1)['exchange']
#         for value in [{}, {'settled':None}, {'settled':{}}, {'settled':''},
#                       {'settled':'completed','exchange':record(2)['exchange']}]:
#             with self.subTest(value=value):
#                 self.f.script(stdout=json.dumps(value)+'\n')
#                 reply = settle(self.f.context, name)
#                 self.assertEqual(reply.status, 1)
#                 self.assertEqual(reply.value['results'][0]['error']['code'], 'trunk_unavailable')
# LOW-TIER-SOURCE-END
# LOW-TIER-END
