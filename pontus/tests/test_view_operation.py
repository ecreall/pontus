# Copyright (c) 2026 by Logikascium under licence AGPL terms
# available on http://www.gnu.org/licenses/agpl.html

# licence: AGPL
# author: Michaël Launay

"""Tests of the pontus ``Wizard`` machinery (T2b).

Characterisation in the functional harness. The headline finding —
pinned as-is: **``Wizard.update()`` has never been able to run.**
Two distinct latent bugs, both pinned: (1) with plain steps the
session is never written (``init_stepid`` is only called by
FormView/MultipleView paths), so ``update()`` walks the whole chain
and dies on the FINAL unconditional session ``__delitem__``
(``KeyError``); (2) with a primed session the resume branch reads
``self.viewsinstances`` — an attribute no code path ever creates (the
constructor builds ``nodes``) — and raises ``AttributeError``. The
51 % baseline agreed: those lines had never run anywhere. Fixing the
wizard must flip both update tests consciously.

Everything AROUND update works and is pinned here: graph construction
(synthetic start/end, transition ids), the session auto-write, the
``Transition.validate`` conditions, the progression-bar math
(``_count_path``, ``_calculate_wizard_informations``), its rendering,
``get_view_requirements`` and the ``success`` redirect.
"""
from pyramid.httpexceptions import HTTPFound

from pontus.testing import FunctionalTests
from pontus.view import BasicView
from pontus.view_operation import Wizard
from pontus.core import STEPID


class StepA(BasicView):
    title = 'Step A'
    name = 'stepa'
    template = 'pontus:tests/example/templates/testtemplate.pt'


class StepB(BasicView):
    title = 'Step B'
    name = 'stepb'
    template = 'pontus:tests/example/templates/testtemplate.pt'


class StepC(BasicView):
    title = 'Step C'
    name = 'stepc'
    template = 'pontus:tests/example/templates/testtemplate.pt'


class ChainWizard(Wizard):
    name = 'chainwizard'
    views = {'a': StepA, 'b': StepB}
    transitions = (('a', 'b'),)


class BranchWizard(Wizard):
    name = 'branchwizard'
    views = {'a': StepA, 'b': StepB, 'c': StepC}
    transitions = (('a', 'b', False, lambda context, request: False),
                   ('a', 'c', True))


class TestWizard(FunctionalTests):

    def test_construction_topology(self):
        wizard = ChainWizard(self.app, self.request)
        self.assertEqual(sorted(wizard.nodes), ['a', 'b'])
        start = wizard.startnode.stepid
        end = wizard.endnode.stepid
        self.assertTrue(start.startswith('start_chainwizard'))
        self.assertTrue(end.startswith('end_chainwizard'))
        self.assertEqual(
            sorted(wizard.transitionsinstances),
            sorted(['a->b', start + '->a', 'b->' + end]))
        self.assertEqual([s.stepid for s in wizard.currentsteps], ['a'])

    def test_branch_topology(self):
        wizard = BranchWizard(self.app, self.request)
        start = wizard.startnode.stepid
        end = wizard.endnode.stepid
        # b and c are both final: two synthetic end transitions
        self.assertEqual(
            sorted(wizard.transitionsinstances),
            sorted(['a->b', 'a->c', start + '->a',
                    'b->' + end, 'c->' + end]))
        self.assertEqual([s.stepid for s in wizard.currentsteps], ['a'])

    def test_construction_leaves_the_session_untouched(self):
        wizard = ChainWizard(self.app, self.request)
        key = STEPID + wizard.viewid
        # init_stepid is a Form/MultipleView affair: plain BasicView
        # steps never write the session
        self.assertIsNone(self.request.session.get(key))

    def test_transition_validate(self):
        wizard = BranchWizard(self.app, self.request)
        # explicit False condition; no behaviour wizard is bound
        self.assertIs(wizard.transitionsinstances['a->b'].validate(),
                      False)
        # default condition answers True
        self.assertIs(wizard.transitionsinstances['a->c'].validate(),
                      True)
        self.assertIs(wizard.transitionsinstances['a->c'].isdefault, True)

    def test_update_walks_the_chain_to_success(self):
        """FIXED (2026-07-17, was latent bug #1): the final cleanup is
        now tolerant (``session.pop(key, None)``) — the chain walks to
        the end and the wizard closes on the success redirect.
        """
        wizard = ChainWizard(self.app, self.request)
        result = wizard.update()
        self.assertIs(result['view'], wizard.nodes['b'])
        self.assertIs(wizard.finished_successfully, True)
        self.assertNotIn(STEPID + wizard.viewid, self.request.session)

    def test_update_primed_resumes_and_completes(self):
        """FIXED (2026-07-17, was latent bug #2): the resume branch now
        reads ``self.nodes`` — the mirror of the constructor — and the
        primed wizard resumes from the stored step to completion.
        """
        wizard = ChainWizard(self.app, self.request)
        self.request.session[STEPID + wizard.viewid] = 'a'
        result = wizard.update()
        # resumes at 'a' and walks to the terminal step
        self.assertIs(result['view'], wizard.nodes['b'])
        self.assertIs(wizard.finished_successfully, True)
        self.assertNotIn(STEPID + wizard.viewid, self.request.session)

    def test_progression_math(self):
        wizard = ChainWizard(self.app, self.request)
        key = STEPID + wizard.viewid
        self.request.session[key] = 'a'
        step, total, covered, rest, percent = \
            wizard._calculate_wizard_informations()
        self.assertIs(step, wizard.nodes['a'])
        self.assertEqual((total, covered, rest, percent), (1, 0, 1, 0.0))
        self.request.session[key] = 'b'
        step, total, covered, rest, percent = \
            wizard._calculate_wizard_informations()
        self.assertIs(step, wizard.nodes['b'])
        self.assertEqual((total, covered, rest, percent),
                         (1, 1, 0, 100.0))

    def test_progression_bar_renders(self):
        wizard = ChainWizard(self.app, self.request)
        self.request.session[STEPID + wizard.viewid] = 'b'
        result = wizard.getwizardinformationsview()
        self.assertEqual(sorted(result), ['body', 'css_links', 'js_links'])
        self.assertIn('Step B', result['body'])
        self.assertIn('100', result['body'])

    def test_get_view_requirements_follows_the_session(self):
        wizard = ChainWizard(self.app, self.request)
        self.request.session[STEPID + wizard.viewid] = 'b'
        requirements = wizard.get_view_requirements()
        self.assertEqual([s.stepid for s in wizard.currentsteps], ['b'])
        self.assertIsInstance(requirements, dict)

    def test_success_redirects_to_index(self):
        wizard = ChainWizard(self.app, self.request)
        # mgmt_path is a substanced request-method; stub it here
        self.request.mgmt_path = (
            lambda context, name: '/app/' + name)
        response = wizard.success()
        self.assertIsInstance(response, HTTPFound)
        self.assertTrue(response.location.endswith('@@index'))
