from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from arbol_root.input import FORWARD, parse  # noqa: E402
from arbol_root.launcher import Reply, select_build  # noqa: E402
from arbol_root.model import Identity, Refusal  # noqa: E402

EXCHANGE = '7f3a2c1e-4b5d-4e6f-8a9b-0c1d2e3f4a5b'
BASE = ['start','--exchange',EXCHANGE,'--request','request.json']
INVENTORY: dict[str, Any] = {'root':'sapling','rootContract':1,'trunks':[{'trunk':'trivial','builds':[
    {'build':'a','status':'working','fits':True,'runnable':True,'chosen':True},
    {'build':'9','status':'withdrawn','fits':True,'runnable':True,'chosen':False},
    {'build':'8','status':'working','fits':False,'runnable':True,'chosen':False}]}]}


class Selection(unittest.TestCase):
    context = Identity('sapling','0','1.0.0',Path('/private-fixture/root'),Path('/private-fixture/bin'))

    def test_input_preserves_run_option_order_spelling_and_values(self) -> None:
        """root.start-input"""
        options = ['--model=two words','--chat','a','--effort','-leading','--driver=claude']
        # A value beginning with '-' uses the documented equals form.
        options[3:5] = ['--effort=-leading']
        command = parse(['--root=sapling',*BASE,'advanced',*options])
        self.assertEqual((command.name,command.code), ('start','advanced'))
        self.assertEqual(command.forward, options)
        self.assertEqual(parse([*BASE,'-v','a']).options['-v'], 'a')
        self.assertEqual(parse(['list']).name, 'list')
        for option in sorted(FORWARD):
            self.assertIn(option, parse([*BASE,option,'value']).options)

    def test_invalid_start_input_is_refused_before_selection(self) -> None:
        for args in [[],['start'],['start','--exchange',EXCHANGE],['start','--request','x'],
                     ['start','--exchange','not-uuid','--request','x'],[*BASE,'x','y'],[*BASE,'--detach'],
                     [*BASE,'--root=sapling','--root=sapling'],[*BASE,'--model='],[*BASE,'--request','other'],
                     ['-v','a',*BASE],['list','--exchange',EXCHANGE],['list','extra'],[*BASE,'-v','0'],[*BASE,'-v','A']]:
            with self.subTest(args=args), self.assertRaises(Refusal) as error:
                parse(args)
            self.assertEqual(error.exception.code, 'invalid_input')

    def test_explicit_build_does_not_query_the_launcher(self) -> None:
        """root.start-named"""
        with mock.patch('arbol_root.launcher.list_reply') as query:
            self.assertEqual(select_build(self.context, parse([*BASE,'-v','b'])), 'b')
        query.assert_not_called()

    def test_uses_the_chosen_build_from_exact_root_and_trunk_inventory(self) -> None:
        """root.start-chosen"""
        with mock.patch('arbol_root.launcher.list_reply', return_value=Reply(b'{}',copy.deepcopy(INVENTORY),0)) as query:
            self.assertEqual(select_build(self.context, parse(BASE)), 'a')
        query.assert_called_once_with('sapling',['trivial'],self.context.bin_dir)

    def test_no_fit_lists_only_fitting_runnable_build_numbers_without_starting(self) -> None:
        """root.start-no-fit"""
        value = copy.deepcopy(INVENTORY)
        value['trunks'][0]['builds'][0]['chosen'] = False
        with mock.patch('arbol_root.launcher.list_reply', return_value=Reply(b'{}',value,0)):
            with self.assertRaises(Refusal) as error:
                select_build(self.context, parse(BASE))
        self.assertEqual((error.exception.code,error.exception.available), ('no_fit',['a','9']))

    def test_launcher_refusal_is_the_same_raw_reply(self) -> None:
        """root.start-selection-refusal"""
        reply = Reply(b' {"error":{"code":"unknown_trunk"},"available":[]}\n', {'error':{'code':'unknown_trunk'}},1)
        with mock.patch('arbol_root.launcher.list_reply', return_value=reply):
            self.assertIs(select_build(self.context, parse(BASE)), reply)

    def test_malformed_or_wrong_inventory_is_unavailable(self) -> None:
        variants = [{}, {**INVENTORY,'root':'other'}, {**INVENTORY,'rootContract':True}, {**INVENTORY,'trunks':[]}]
        duplicate = copy.deepcopy(INVENTORY)
        duplicate['trunks'][0]['builds'][1]['chosen'] = True
        variants.append(duplicate)
        for value in variants:
            with self.subTest(value=value), mock.patch('arbol_root.launcher.list_reply', return_value=Reply(b'{}',value,0)):
                with self.assertRaises(Refusal) as error:
                    select_build(self.context, parse(BASE))
                self.assertEqual(error.exception.code, 'trunk_unavailable')
