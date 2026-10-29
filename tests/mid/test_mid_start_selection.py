"""Commented mid-tier selections; see MID_TIER.md before restoring a case."""

# Restore the needed imports and class header only for an explicit testing task.
# import test_start_selection as _support
# from test_start_selection import (
#     Any,
#     BASE,
#     EXCHANGE,
#     INVENTORY,
#     Identity,
#     Path,
#     Selection,
#     sys,
#     unittest,
# )


# class Selection(_support.Selection):
# TEST-TIER-DISABLED-BEGIN tests/test_start_selection.py::Selection.test_input_preserves_run_option_order_spelling_and_values
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
# TEST-TIER-DISABLED-END tests/test_start_selection.py::Selection.test_input_preserves_run_option_order_spelling_and_values

# TEST-TIER-DISABLED-BEGIN tests/test_start_selection.py::Selection.test_invalid_start_input_is_refused_before_selection
#     def test_invalid_start_input_is_refused_before_selection(self) -> None:
#         for args in [[],['start'],['start','--exchange',EXCHANGE],['start','--request','x'],
#                      ['start','--exchange','not-uuid','--request','x'],[*BASE,'x','y'],[*BASE,'--detach'],
#                      [*BASE,'--root=sapling','--root=sapling'],[*BASE,'--model='],[*BASE,'--request','other'],
#                      ['-v','a',*BASE],['list','--exchange',EXCHANGE],['list','extra'],[*BASE,'-v','0'],[*BASE,'-v','A']]:
#             with self.subTest(args=args), self.assertRaises(Refusal) as error:
#                 parse(args)
#             self.assertEqual(error.exception.code, 'invalid_input')
# TEST-TIER-DISABLED-END tests/test_start_selection.py::Selection.test_invalid_start_input_is_refused_before_selection

# TEST-TIER-DISABLED-BEGIN tests/test_start_selection.py::Selection.test_no_fit_lists_only_fitting_runnable_build_numbers_without_starting
#     def test_no_fit_lists_only_fitting_runnable_build_numbers_without_starting(self) -> None:
#         """root.start-no-fit"""
#         value = copy.deepcopy(INVENTORY)
#         value['trunks'][0]['builds'][0]['chosen'] = False
#         with mock.patch('arbol_root.launcher.list_reply', return_value=Reply(b'{}',value,0)):
#             with self.assertRaises(Refusal) as error:
#                 select_build(self.context, parse(BASE))
#         self.assertEqual((error.exception.code,error.exception.available), ('no_fit',['a','9']))
# TEST-TIER-DISABLED-END tests/test_start_selection.py::Selection.test_no_fit_lists_only_fitting_runnable_build_numbers_without_starting

# TEST-TIER-DISABLED-BEGIN tests/test_start_selection.py::Selection.test_malformed_or_wrong_inventory_is_unavailable
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
# TEST-TIER-DISABLED-END tests/test_start_selection.py::Selection.test_malformed_or_wrong_inventory_is_unavailable


# Original deferred imports (restore at the required scope, never blindly at the tail).
# TEST-TIER-IMPORTS-BEGIN tests/test_start_selection.py:3
# import copy
# TEST-TIER-IMPORTS-END tests/test_start_selection.py:3

# TEST-TIER-IMPORTS-BEGIN tests/test_start_selection.py:8
# from unittest import mock
# TEST-TIER-IMPORTS-END tests/test_start_selection.py:8

# TEST-TIER-IMPORTS-BEGIN tests/test_start_selection.py:11
# from arbol_root.input import FORWARD, parse  # noqa: E402
# TEST-TIER-IMPORTS-END tests/test_start_selection.py:11

# TEST-TIER-IMPORTS-BEGIN tests/test_start_selection.py:12
# from arbol_root.launcher import Reply, select_build  # noqa: E402
# TEST-TIER-IMPORTS-END tests/test_start_selection.py:12

# TEST-TIER-IMPORTS-BEGIN tests/test_start_selection.py:13
# from arbol_root.model import Identity, Refusal  # noqa: E402
# TEST-TIER-IMPORTS-END tests/test_start_selection.py:13

raise RuntimeError("Mid-tier tests require an explicitly requested testing task; see MID_TIER.md.")
