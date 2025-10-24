from unittest import TestCase

from tlparser.stats import Stats
from tlparser.stats_ext import SpotAnalyzer
from test_case_data import TestCaseDataExt


EXTENDED_CASES = (
    TestCaseDataExt(
        f_code="G p",
        aps=1,
        syntactic_safety=True,
        is_stutter_invariant_formula=True,
        manna_pnueli_class_contains="Safety",
        tgba_state_count=1,
        tgba_transition_count=1,
        tgba_is_complete=False,
        tgba_is_deterministic=True,
        tgba_acceptance_sets=0,
        tgba_is_stutter_invariant=True,
        buchi_state_count=1,
        buchi_transition_count=1,
        buchi_is_complete=False,
        buchi_is_deterministic=True,
        buchi_acceptance_sets=1,
        buchi_is_stutter_invariant=True,
        det_attempt_success=True,
        det_state_count=1,
        det_transition_count=1,
        det_is_complete=False,
        det_is_deterministic=True,
        det_acceptance_sets=0,
        det_is_stutter_invariant=True,
    ),
    TestCaseDataExt(
        f_code="F G s",
        aps=1,
        syntactic_safety=False,
        is_stutter_invariant_formula=True,
        manna_pnueli_class_contains="persistence reactivity",
        tgba_state_count=2,
        tgba_transition_count=4,
        tgba_is_complete=False,
        tgba_is_deterministic=False,
        tgba_acceptance_sets=1,
        tgba_is_stutter_invariant=True,
        buchi_state_count=2,
        buchi_transition_count=4,
        buchi_is_complete=False,
        buchi_is_deterministic=False,
        buchi_acceptance_sets=1,
        buchi_is_stutter_invariant=True,
        det_attempt_success=True,
        det_state_count=2,
        det_transition_count=4,
        det_is_complete=False,
        det_is_deterministic=False,
        det_acceptance_sets=1,
        det_is_stutter_invariant=True,
    ),
    TestCaseDataExt(
        f_code="G (req --> F ack)",
        aps=2,
        syntactic_safety=False,
        is_stutter_invariant_formula=True,
        manna_pnueli_class_contains="recurrence reactivity",
        tgba_state_count=2,
        tgba_transition_count=8,
        tgba_is_complete=True,
        tgba_is_deterministic=True,
        tgba_acceptance_sets=1,
        tgba_is_stutter_invariant=True,
        buchi_state_count=2,
        buchi_transition_count=8,
        buchi_is_complete=True,
        buchi_is_deterministic=True,
        buchi_acceptance_sets=1,
        buchi_is_stutter_invariant=True,
        det_attempt_success=True,
        det_state_count=2,
        det_transition_count=8,
        det_is_complete=True,
        det_is_deterministic=True,
        det_acceptance_sets=1,
        det_is_stutter_invariant=True,
    ),
    TestCaseDataExt(
        f_code="G (not(crit1 & crit2))",
        aps=2,
        syntactic_safety=True,
        is_stutter_invariant_formula=True,
        manna_pnueli_class_contains="Safety",
        tgba_state_count=1,
        tgba_transition_count=3,
        tgba_is_complete=False,
        tgba_is_deterministic=True,
        tgba_acceptance_sets=0,
        tgba_is_stutter_invariant=True,
        buchi_state_count=1,
        buchi_transition_count=3,
        buchi_is_complete=False,
        buchi_is_deterministic=True,
        buchi_acceptance_sets=1,
        buchi_is_stutter_invariant=True,
        det_attempt_success=True,
        det_state_count=1,
        det_transition_count=3,
        det_is_complete=False,
        det_is_deterministic=True,
        det_acceptance_sets=0,
        det_is_stutter_invariant=True,
    ),
    TestCaseDataExt(
        f_code="GFa --> GFb",
        aps=2,
        syntactic_safety=False,
        is_stutter_invariant_formula=True,
        manna_pnueli_class_contains="reactivity",
        tgba_state_count=3,
        tgba_transition_count=14,
        tgba_is_complete=False,
        tgba_is_deterministic=False,
        tgba_acceptance_sets=1,
        tgba_is_stutter_invariant=True,
        buchi_state_count=4,
        buchi_transition_count=18,
        buchi_is_complete=False,
        buchi_is_deterministic=False,
        buchi_acceptance_sets=1,
        buchi_is_stutter_invariant=True,
        det_attempt_success=True,
        det_state_count=3,
        det_transition_count=14,
        det_is_complete=False,
        det_is_deterministic=False,
        det_acceptance_sets=1,
        det_is_stutter_invariant=True,
    ),
    TestCaseDataExt(
        f_code="X p",
        aps=1,
        syntactic_safety=True,
        is_stutter_invariant_formula=False,
        manna_pnueli_class_contains="guarantee safety obligation persistence recurrence reactivity",
        tgba_state_count=3,
        tgba_transition_count=5,
        tgba_is_complete=False,
        tgba_is_deterministic=True,
        tgba_acceptance_sets=0,
        tgba_is_stutter_invariant=False,
        buchi_state_count=3,
        buchi_transition_count=5,
        buchi_is_complete=False,
        buchi_is_deterministic=True,
        buchi_acceptance_sets=1,
        buchi_is_stutter_invariant=False,
        det_attempt_success=True,
        det_state_count=3,
        det_transition_count=5,
        det_is_complete=False,
        det_is_deterministic=True,
        det_acceptance_sets=0,
        det_is_stutter_invariant=False,
    ),
    TestCaseDataExt(
        f_code="F X p",
        aps=1,
        syntactic_safety=False,
        is_stutter_invariant_formula=False,
        manna_pnueli_class_contains="guarantee obligation persistence recurrence reactivity",
        tgba_state_count=3,
        tgba_transition_count=6,
        tgba_is_complete=True,
        tgba_is_deterministic=True,
        tgba_acceptance_sets=1,
        tgba_is_stutter_invariant=False,
        buchi_state_count=3,
        buchi_transition_count=6,
        buchi_is_complete=True,
        buchi_is_deterministic=True,
        buchi_acceptance_sets=1,
        buchi_is_stutter_invariant=False,
        det_attempt_success=True,
        det_state_count=3,
        det_transition_count=6,
        det_is_complete=True,
        det_is_deterministic=True,
        det_acceptance_sets=1,
        det_is_stutter_invariant=False,
    ),
)


class TestStatsExtended(TestCase):
    def setUp(self):
        # These tests rely on real Spot tooling; they skip automatically when unavailable.
        self.data = EXTENDED_CASES
        self.analyzer = SpotAnalyzer()
        self._stats_cache: dict[str, Stats] = {}

    class _NullAnalyzer:
        def __init__(self):
            self.calls: list[str] = []

        def classify(self, formula: str):
            self.calls.append(formula)
            return None

    def _get_stats(self, case: TestCaseDataExt) -> Stats:
        cached = self._stats_cache.get(case.f_code)
        if cached is not None:
            return cached

        stats = Stats(case.f_code, extended=True, spot_analyzer=self.analyzer)
        if stats.spot is None:
            self.skipTest(
                "Spot CLI tools not available. Install Spot or disable extended tests."
            )
        self._stats_cache[case.f_code] = stats
        return stats

    def test_formula_in_spot_result(self):
        for case in self.data:
            with self.subTest(formula=case.f_code):
                stats = self._get_stats(case)
                self.assertEqual(case.f_code, stats.spot.get("formula"), case.f_code)

    def test_spot_reports_tgba_analysis(self):
        for case in self.data:
            with self.subTest(formula=case.f_code):
                stats = self._get_stats(case)
                self.assertIn("tgba_analysis", stats.spot, case.f_code)

    def test_spot_respects_syntactic_safety(self):
        for case in self.data:
            with self.subTest(formula=case.f_code):
                stats = self._get_stats(case)
                self.assertEqual(case.syntactic_safety, stats.spot.get("syntactic_safety"), case.f_code)

    def test_spot_respects_stutter_invariance(self):
        for case in self.data:
            with self.subTest(formula=case.f_code):
                stats = self._get_stats(case)
                self.assertEqual(
                    case.is_stutter_invariant_formula,
                    stats.spot.get("is_stutter_invariant_formula"),
                    case.f_code,
                )

    def test_spot_reports_manna_pnueli_class(self):
        for case in self.data:
            with self.subTest(formula=case.f_code):
                stats = self._get_stats(case)
                actual_class = stats.spot.get("manna_pnueli_class", "") or ""
                self.assertIn(case.manna_pnueli_class_contains.lower(), actual_class.lower(), case.f_code)

    def test_aggregated_ap_matches_expectation(self):
        for case in self.data:
            with self.subTest(formula=case.f_code):
                stats = self._get_stats(case)
                self.assertEqual(case.aps, stats.agg["aps"], case.f_code)

    def test_spot_formula_translation(self):
        expected_substrings = {
            "G (req --> F ack)": "req -> F ack",
            "G (not(crit1 & crit2))": "!(crit1 & crit2)",
            "GFa --> GFb": "GFa -> GFb",
        }
        for case in self.data:
            with self.subTest(formula=case.f_code):
                stats = self._get_stats(case)
                spot_formula = stats.spot.get("spot_formula")
                self.assertIsNotNone(spot_formula, case.f_code)
                expected = expected_substrings.get(case.f_code)
                if expected is None:
                    self.assertEqual(case.f_code, spot_formula, case.f_code)
                else:
                    self.assertIn(expected, spot_formula, case.f_code)

    def test_tgba_state_count(self):
        for case in self.data:
            with self.subTest(formula=case.f_code):
                stats = self._get_stats(case)
                self.assertEqual(
                    case.tgba_state_count,
                    stats.spot.get("tgba_analysis", {}).get("state_count"),
                    case.f_code,
                )

    def test_tgba_transition_count(self):
        for case in self.data:
            with self.subTest(formula=case.f_code):
                stats = self._get_stats(case)
                self.assertEqual(
                    case.tgba_transition_count,
                    stats.spot.get("tgba_analysis", {}).get("transition_count"),
                    case.f_code,
                )

    def test_tgba_is_complete(self):
        for case in self.data:
            with self.subTest(formula=case.f_code):
                stats = self._get_stats(case)
                self.assertEqual(
                    case.tgba_is_complete,
                    stats.spot.get("tgba_analysis", {}).get("is_complete"),
                    case.f_code,
                )

    def test_tgba_is_deterministic(self):
        for case in self.data:
            with self.subTest(formula=case.f_code):
                stats = self._get_stats(case)
                self.assertEqual(
                    case.tgba_is_deterministic,
                    stats.spot.get("tgba_analysis", {}).get("is_deterministic"),
                    case.f_code,
                )

    def test_tgba_acceptance_sets(self):
        for case in self.data:
            with self.subTest(formula=case.f_code):
                stats = self._get_stats(case)
                self.assertEqual(
                    case.tgba_acceptance_sets,
                    stats.spot.get("tgba_analysis", {}).get("acceptance_sets"),
                    case.f_code,
                )

    def test_tgba_is_stutter_invariant(self):
        for case in self.data:
            with self.subTest(formula=case.f_code):
                stats = self._get_stats(case)
                self.assertEqual(
                    case.tgba_is_stutter_invariant,
                    stats.spot.get("tgba_analysis", {}).get("is_stutter_invariant"),
                    case.f_code,
                )

    def test_buchi_state_count(self):
        for case in self.data:
            with self.subTest(formula=case.f_code):
                stats = self._get_stats(case)
                self.assertEqual(
                    case.buchi_state_count,
                    stats.spot.get("buchi_analysis", {}).get("state_count"),
                    case.f_code,
                )

    def test_buchi_transition_count(self):
        for case in self.data:
            with self.subTest(formula=case.f_code):
                stats = self._get_stats(case)
                self.assertEqual(
                    case.buchi_transition_count,
                    stats.spot.get("buchi_analysis", {}).get("transition_count"),
                    case.f_code,
                )

    def test_buchi_is_complete(self):
        for case in self.data:
            with self.subTest(formula=case.f_code):
                stats = self._get_stats(case)
                self.assertEqual(
                    case.buchi_is_complete,
                    stats.spot.get("buchi_analysis", {}).get("is_complete"),
                    case.f_code,
                )

    def test_buchi_is_deterministic(self):
        for case in self.data:
            with self.subTest(formula=case.f_code):
                stats = self._get_stats(case)
                self.assertEqual(
                    case.buchi_is_deterministic,
                    stats.spot.get("buchi_analysis", {}).get("is_deterministic"),
                    case.f_code,
                )

    def test_buchi_acceptance_sets(self):
        for case in self.data:
            with self.subTest(formula=case.f_code):
                stats = self._get_stats(case)
                self.assertEqual(
                    case.buchi_acceptance_sets,
                    stats.spot.get("buchi_analysis", {}).get("acceptance_sets"),
                    case.f_code,
                )

    def test_buchi_is_stutter_invariant(self):
        for case in self.data:
            with self.subTest(formula=case.f_code):
                stats = self._get_stats(case)
                self.assertEqual(
                    case.buchi_is_stutter_invariant,
                    stats.spot.get("buchi_analysis", {}).get("is_stutter_invariant"),
                    case.f_code,
                )

    def test_deterministic_attempt_success(self):
        for case in self.data:
            with self.subTest(formula=case.f_code):
                stats = self._get_stats(case)
                self.assertEqual(
                    case.det_attempt_success,
                    stats.spot.get("deterministic_attempt", {}).get("success"),
                    case.f_code,
                )

    def test_deterministic_state_count(self):
        for case in self.data:
            with self.subTest(formula=case.f_code):
                stats = self._get_stats(case)
                self.assertEqual(
                    case.det_state_count,
                    stats.spot.get("deterministic_attempt", {})
                    .get("automaton_analysis", {})
                    .get("state_count"),
                    case.f_code,
                )

    def test_deterministic_transition_count(self):
        for case in self.data:
            with self.subTest(formula=case.f_code):
                stats = self._get_stats(case)
                self.assertEqual(
                    case.det_transition_count,
                    stats.spot.get("deterministic_attempt", {})
                    .get("automaton_analysis", {})
                    .get("transition_count"),
                    case.f_code,
                )

    def test_deterministic_is_complete(self):
        for case in self.data:
            with self.subTest(formula=case.f_code):
                stats = self._get_stats(case)
                self.assertEqual(
                    case.det_is_complete,
                    stats.spot.get("deterministic_attempt", {})
                    .get("automaton_analysis", {})
                    .get("is_complete"),
                    case.f_code,
                )

    def test_deterministic_is_deterministic(self):
        for case in self.data:
            with self.subTest(formula=case.f_code):
                stats = self._get_stats(case)
                self.assertEqual(
                    case.det_is_deterministic,
                    stats.spot.get("deterministic_attempt", {})
                    .get("automaton_analysis", {})
                    .get("is_deterministic"),
                    case.f_code,
                )

    def test_deterministic_acceptance_sets(self):
        for case in self.data:
            with self.subTest(formula=case.f_code):
                stats = self._get_stats(case)
                self.assertEqual(
                    case.det_acceptance_sets,
                    stats.spot.get("deterministic_attempt", {})
                    .get("automaton_analysis", {})
                    .get("acceptance_sets"),
                    case.f_code,
                )

    def test_deterministic_is_stutter_invariant(self):
        for case in self.data:
            with self.subTest(formula=case.f_code):
                stats = self._get_stats(case)
                self.assertEqual(
                    case.det_is_stutter_invariant,
                    stats.spot.get("deterministic_attempt", {})
                    .get("automaton_analysis", {})
                    .get("is_stutter_invariant"),
                    case.f_code,
                )

    def _get_null_analyzer_results(self):
        analyzer = self._NullAnalyzer()
        stats_by_case: dict[str, Stats] = {}
        for case in self.data:
            stats_by_case[case.f_code] = Stats(
                case.f_code,
                extended=True,
                spot_analyzer=analyzer,
            )
        return analyzer, stats_by_case

    def test_null_analyzer_records_calls(self):
        analyzer, _ = self._get_null_analyzer_results()
        for case in self.data:
            with self.subTest(formula=case.f_code):
                self.assertIn(case.f_code, analyzer.calls, case.f_code)

    def test_null_analyzer_returns_no_spot_stats(self):
        _, stats_by_case = self._get_null_analyzer_results()
        for case in self.data:
            with self.subTest(formula=case.f_code):
                self.assertIsNone(stats_by_case[case.f_code].spot, case.f_code)

    def test_null_analyzer_keeps_ap_counts(self):
        _, stats_by_case = self._get_null_analyzer_results()
        for case in self.data:
            with self.subTest(formula=case.f_code):
                self.assertEqual(case.aps, stats_by_case[case.f_code].agg["aps"], case.f_code)
