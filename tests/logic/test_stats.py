from unittest import TestCase

from tlparser.stats import Stats
from test_case_data import TestCaseData


STATS_TEST_CASES = (
    TestCaseData(f_code="p --> q", asth=1, aps=2, cops=0, lops=1, tops=0),
    TestCaseData(f_code="p == 0 --> q", asth=1, aps=2, cops=1, lops=1, tops=0),
    TestCaseData(
        f_code="G((y and u == 9) --> F(not y or i < 3))",
        asth=5,
        aps=3,
        cops=2,
        lops=4,
        tops=2,
        entropy_lops_tops=2.585,
    ),
    TestCaseData(
        f_code="G((x and (u == 9) and (i < 3)) --> G(not y or x))",
        asth=5,
        aps=4,
        cops=2,
        lops=5,
        tops=2,
    ),
    TestCaseData(
        f_code="G(Number_of_FCTs <= 7)", asth=1, aps=1, cops=1, lops=0, tops=1
    ),
    TestCaseData(
        f_code="G(Number_of_FCTs >= seven)",
        asth=1,
        aps=1,
        cops=1,
        lops=0,
        tops=1,
    ),
    TestCaseData(
        f_code="G(((ss) --> F(ers))) and G((cs) --> F(not (fct) --> (ers)))",
        asth=6,
        aps=4,
        cops=0,
        lops=5,
        tops=4,
    ),
    TestCaseData(
        f_code="G((im) --> ((ics) --> F(ics --> disc))) and I == citt",
        asth=6,
        aps=4,
        cops=1,
        lops=4,
        tops=2,
    ),
    TestCaseData(
        f_code="G((a or b) --> X(c >= 9 and c <= 11))",
        asth=4,
        aps=4,
        cops=2,
        lops=3,
        tops=2,
    ),
    TestCaseData(
        f_code="G((mode) --> (a)) and I == cit",
        asth=3,
        aps=3,
        cops=1,
        lops=2,
        tops=1,
    ),
    TestCaseData(
        f_code="(ics) --> F((ics) --> (new))",
        asth=3,
        aps=2,
        cops=0,
        lops=2,
        tops=1,
    ),
    TestCaseData(
        f_code="G((mode) --> ((ics) --> F((ics) --> (new)))) and I == cit",
        asth=6,
        aps=4,
        cops=1,
        lops=4,
        tops=2,
    ),
    TestCaseData(
        f_code="G(sr --> ((s == x or s == y) and (not (s == x and s == y)) and x == n and y == m))",
        asth=5,
        aps=5,
        cops=6,
        lops=7,
        tops=1,
    ),
    TestCaseData(
        f_code="G(((a) --> ((b) and not(c or EEP))) --> X(((d) and (f)) U((EOPr or EEPr) and (EOPd or EEPc))))",
        asth=6,
        aps=10,
        cops=0,
        lops=9,
        tops=3,
    ),
    TestCaseData(
        f_code="G( (receive_i --> X(F(receive_j))) --> (send_i and X(send_j)) )",
        asth=5,
        aps=4,
        cops=0,
        lops=3,
        tops=4,
    ),
    TestCaseData(
        f_code="G(   ( ((cicr)) --> X not(not(sia) U(icp)) ) --> ( G(nicd) and G(F(nicp)) )   )",
        asth=7,
        aps=5,
        cops=0,
        lops=5,
        tops=6,
    ),
    TestCaseData(
        f_code="G (not(five < waitCPU))",
        asth=2,
        aps=1,
        cops=1,
        lops=1,
        tops=1,
    ),
    TestCaseData(
        f_code="G (not (waitCPU > five))",
        asth=2,
        aps=1,
        cops=1,
        lops=1,
        tops=1,
    ),
    TestCaseData(
        f_code="G (not (5 < waitCPU))",
        asth=2,
        aps=1,
        cops=1,
        lops=1,
        tops=1,
    ),
    TestCaseData(
        f_code="G (not (waitCPU > 5))",
        asth=2,
        aps=1,
        cops=1,
        lops=1,
        tops=1,
    ),
)


class TestStats(TestCase):
    def setUp(self):

        self.data = STATS_TEST_CASES


class TestInit(TestStats):

    def test_ast(self):
        for case in self.data:
            f = Stats(case.f_code)
            self.assertEqual(case.asth, f.asth, case.f_code)

    def test_aps(self):
        for case in self.data:
            f = Stats(case.f_code)
            self.assertEqual(case.aps, f.agg["aps"], case.f_code)

    def test_cops(self):
        for case in self.data:
            f = Stats(case.f_code)
            self.assertEqual(case.cops, f.agg["cops"], case.f_code)

    def test_lops(self):
        for case in self.data:
            f = Stats(case.f_code)
            self.assertEqual(case.lops, f.agg["lops"], case.f_code)

    def test_tops(self):
        for case in self.data:
            f = Stats(case.f_code)
            self.assertEqual(case.tops, f.agg["tops"], case.f_code)

    def test_entropy(self):
        for case in self.data:
            if case.entropy_lops_tops is not None:
                f = Stats(case.f_code)
                self.assertEqual(
                    case.entropy_lops_tops,
                    round(f.entropy["lops_tops"], 3),
                    case.f_code,
                )
