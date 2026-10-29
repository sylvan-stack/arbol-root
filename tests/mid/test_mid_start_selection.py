
# LOW TIER — DO NOT ENABLE OR RECREATE
# Historical examples only. Read before adding related tests; never execute.
# LOW-TIER-BEGIN: tests/mid/test_mid_start_selection.py::Selection.test_input_preserves_run_option_order_spelling_and_values
# Reason: Selection and argument tables restate straightforward parsing and inventory branches. Case reviewed: root.start-input
# Source: arbol-root@ef4fd6a30eca7130653b20e5eedf0da7be72aaa4:tests/mid/test_mid_start_selection.py
# Historical fixtures and class context are available at the source revision; no active dependencies restored.
# LOW-TIER-SOURCE-BEGIN
#     def test_input_preserves_run_option_order_spelling_and_values(self) -> None:
#         """root.start-input"""
#         options = ['--model=two words','--chat','a','--effort','-leading','--driver=claude']
#         # A value beginning with '-' uses the documented equals form.
#         options[3:5] = ['--effort=-leading']
#         command = parse(['--root=sapling',*BASE,'advanced',*options])
#         self.assertEqual((command.name,command.code), ('start','advanced'))
#         self.assertEqual(command.forward, options)
#         self.assertEqual(parse([*BASE,'-v','a']).options['-v'], 'a')
#         self.assertEqual(parse(['list']).name, 'list')
#         for option in sorted(FORWARD):
#             self.assertIn(option, parse([*BASE,option,'value']).options)
# LOW-TIER-SOURCE-END
# LOW-TIER-END

# LOW-TIER-BEGIN: tests/mid/test_mid_start_selection.py::Selection.test_invalid_start_input_is_refused_before_selection
# Reason: Selection and argument tables restate straightforward parsing and inventory branches. Case reviewed: Invalid start input is refused before selection.
# Source: arbol-root@ef4fd6a30eca7130653b20e5eedf0da7be72aaa4:tests/mid/test_mid_start_selection.py
# Historical fixtures and class context are available at the source revision; no active dependencies restored.
# LOW-TIER-SOURCE-BEGIN
#     def test_invalid_start_input_is_refused_before_selection(self) -> None:
#         for args in [[],['start'],['start','--exchange',EXCHANGE],['start','--request','x'],
#                      ['start','--exchange','not-uuid','--request','x'],[*BASE,'x','y'],[*BASE,'--detach'],
#                      [*BASE,'--root=sapling','--root=sapling'],[*BASE,'--model='],[*BASE,'--request','other'],
#                      ['-v','a',*BASE],['list','--exchange',EXCHANGE],['list','extra'],[*BASE,'-v','0'],[*BASE,'-v','A']]:
#             with self.subTest(args=args), self.assertRaises(Refusal) as error:
#                 parse(args)
#             self.assertEqual(error.exception.code, 'invalid_input')
# LOW-TIER-SOURCE-END
# LOW-TIER-END

# LOW-TIER-BEGIN: tests/mid/test_mid_start_selection.py::Selection.test_no_fit_lists_only_fitting_runnable_build_numbers_without_starting
# Reason: Selection and argument tables restate straightforward parsing and inventory branches. Case reviewed: root.start-no-fit
# Source: arbol-root@ef4fd6a30eca7130653b20e5eedf0da7be72aaa4:tests/mid/test_mid_start_selection.py
# Historical fixtures and class context are available at the source revision; no active dependencies restored.
# LOW-TIER-SOURCE-BEGIN
#     def test_no_fit_lists_only_fitting_runnable_build_numbers_without_starting(self) -> None:
#         """root.start-no-fit"""
#         value = copy.deepcopy(INVENTORY)
#         value['trunks'][0]['builds'][0]['chosen'] = False
#         with mock.patch('arbol_root.launcher.list_reply', return_value=Reply(b'{}',value,0)):
#             with self.assertRaises(Refusal) as error:
#                 select_build(self.context, parse(BASE))
#         self.assertEqual((error.exception.code,error.exception.available), ('no_fit',['a','9']))
# LOW-TIER-SOURCE-END
# LOW-TIER-END

# LOW-TIER-BEGIN: tests/mid/test_mid_start_selection.py::Selection.test_malformed_or_wrong_inventory_is_unavailable
# Reason: Selection and argument tables restate straightforward parsing and inventory branches. Case reviewed: Malformed or wrong inventory is unavailable.
# Source: arbol-root@ef4fd6a30eca7130653b20e5eedf0da7be72aaa4:tests/mid/test_mid_start_selection.py
# Historical fixtures and class context are available at the source revision; no active dependencies restored.
# LOW-TIER-SOURCE-BEGIN
#     def test_malformed_or_wrong_inventory_is_unavailable(self) -> None:
#         variants = [{}, {**INVENTORY,'root':'other'}, {**INVENTORY,'rootContract':True}, {**INVENTORY,'trunks':[]}]
#         duplicate = copy.deepcopy(INVENTORY)
#         duplicate['trunks'][0]['builds'][1]['chosen'] = True
#         variants.append(duplicate)
#         for value in variants:
#             with self.subTest(value=value), mock.patch('arbol_root.launcher.list_reply', return_value=Reply(b'{}',value,0)):
#                 with self.assertRaises(Refusal) as error:
#                     select_build(self.context, parse(BASE))
#                 self.assertEqual(error.exception.code, 'trunk_unavailable')
# LOW-TIER-SOURCE-END
# LOW-TIER-END
