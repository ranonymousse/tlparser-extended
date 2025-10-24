from __future__ import annotations

from pyModelChecking import CTLS
import re
import pprint
from scipy.stats import entropy
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tlparser.stats_ext import SpotAnalyzer

try:  # pragma: no cover - guard against optional Spot dependencies missing
    from tlparser.stats_ext import SpotAnalyzer as _SpotAnalyzer
except Exception:  # noqa: BLE001
    _SpotAnalyzer = None


class Stats:
    def __init__(
        self,
        formula_str,
        req_text=None,
        *,
        extended: bool = False,
        spot_analyzer: "SpotAnalyzer" | None = None,
        spot_verbose: bool = False,
    ):
        self.formula_raw = formula_str
        self.formula_parsable = None
        self.formula_parsed = None
        self.spot = None

        req_text_stats = self.get_requirement_text_stats(req_text)
        self.req_len = req_text_stats[0]
        self.req_word_count = req_text_stats[1]
        self.req_sentence_count = req_text_stats[2]

        # Group: Comparison operators
        self.cops = {
            "eq": 0,  # Equal
            "neq": 0,  # Not equal
            "gt": 0,  # Greater than
            "geq": 0,  # Greater than or equal
            "lt": 0,  # Less than
            "leq": 0,  # Less than or equal
        }

        # Group: Temporal operators
        self.tops = {
            "A": 0,  # For all
            "E": 0,  # Exists
            "X": 0,  # Next
            "F": 0,  # Finally
            "G": 0,  # Globally
            "U": 0,  # Until
            "R": 0,  # Release
        }

        # Group: Logical operators
        self.lops = {
            "impl": 0,  # Implication
            "and": 0,  # And
            "or": 0,  # Or
            "not": 0,  # Not
        }

        # Other properties
        self.asth = 0
        self.ap = set()  # Atomic propositions (e.g., 'x > 5')

        if len(self.formula_raw) > 0:
            # Replace comparison operators
            self.cops, self.formula_parsable = self.analyse_comparison_ops(
                self.formula_raw
            )

            # Parse the formula
            p = CTLS.Parser()
            self.formula_parsed = p(self.formula_parsable)
            self.analyze_formula(self.formula_parsed)
            self.agg = self.update_aggregates()
            self.entropy = self.calc_entropy()

            if extended:
                analyzer = spot_analyzer
                if analyzer is None and _SpotAnalyzer is not None:
                    analyzer = _SpotAnalyzer(verbose=spot_verbose)
                if analyzer is not None:
                    self.spot = analyzer.classify(self.formula_raw)

    @staticmethod
    def analyse_comparison_ops(formula_str):
        # Patterns for comparison operators
        patterns = {
            "eq": re.compile(r"=="),
            "leq": re.compile(r"<="),
            "geq": re.compile(r">="),
            "neq": re.compile(r"!="),
            "lt": re.compile(r"(?<!<)<(?![=<])"),  # Ensure it does not match <=
            "gt": re.compile(r"(?<!>)>(?![=>])"),  # Ensure it does not match >=
        }

        # Count occurrences of each operator
        formula_tmp = re.sub("-->", "__IMPLIES__", formula_str)
        counts = {
            key: len(pattern.findall(formula_tmp)) for key, pattern in patterns.items()
        }

        # Sub-function to replace comparison operators
        def replace_comparisons(match):
            expression = match.group().replace(" ", "")
            expression = re.sub(r"-", "n", expression)
            if "<=" in expression:
                return expression.replace("<=", "_leq_")
            elif ">=" in expression:
                return expression.replace(">=", "_geq_")
            elif "==" in expression:
                return expression.replace("==", "_eq_")
            elif "!=" in expression:
                return expression.replace("!=", "_neq_")
            elif "<" in expression:
                return expression.replace("<", "_lt_")
            elif ">" in expression:
                return expression.replace(">", "_gt_")

        # Replace comparison operators (allowing for any amount of space)
        modified_string = re.sub(
            r"\b[\w.]+ *[<>!=]=? *-?\w+\b", replace_comparisons, formula_str
        )

        # Add 'n' before every number
        modified_string = re.sub(r"(\d+(\.\d+)?)", r"n\1", modified_string)

        return counts, modified_string

    def analyze_formula(self, node, level=0):
        if level == 0:
            self.asth = node.height

        if isinstance(node, CTLS.AtomicProposition):
            self.ap.add(str(node))
            return  # Atomic propositions don't have further nesting

        if isinstance(node, CTLS.Imply):
            self.lops["impl"] += 1
        if isinstance(node, CTLS.And):
            self.lops["and"] += len(node._subformula) - 1
        if isinstance(node, CTLS.Or):
            self.lops["or"] += len(node._subformula) - 1
        if isinstance(node, CTLS.Not):
            self.lops["not"] += 1

        if isinstance(node, CTLS.X):
            self.tops["X"] += 1
        if isinstance(node, CTLS.F):
            self.tops["F"] += 1
        if isinstance(node, CTLS.G):
            self.tops["G"] += 1
        if isinstance(node, CTLS.U):
            self.tops["U"] += 1
        if isinstance(node, CTLS.R):
            self.tops["R"] += 1
        if isinstance(node, CTLS.A):
            self.tops["A"] += 1
        if isinstance(node, CTLS.E):
            self.tops["E"] += 1

        # Recursively analyze subformulas
        if hasattr(node, "_subformula"):
            for subformula in node._subformula:
                self.analyze_formula(subformula, level + 1)
        else:
            raise ValueError("Unknown node type")

    def update_aggregates(self):
        return {
            "aps": len(self.ap),
            "cops": sum(self.cops.values()),
            "lops": sum(self.lops.values()),
            "tops": sum(self.tops.values()),
        }

    def calc_entropy(self):
        entr_tops = entropy(list(self.tops.values()), base=2)
        entr_lops = entropy(list(self.lops.values()), base=2)
        tops_lops = self.tops.copy()
        tops_lops.update(self.lops)
        entr_tops_lops = entropy(list(tops_lops.values()), base=2)

        return {
            "lops": entr_tops,
            "tops": entr_lops,
            "lops_tops": entr_tops_lops,
        }

    def get_stats(self):
        return {key: value for key, value in vars(self).items() if key not in [""]}

    def as_serializable(self):
        sanitized = self._sanitize_for_json(self.get_stats())
        spot_data = sanitized.pop("spot", None)
        if spot_data:
            sanitized["z_extended"] = spot_data
        return sanitized

    @staticmethod
    def _sanitize_for_json(value):
        if isinstance(value, dict):
            return {k: Stats._sanitize_for_json(v) for k, v in value.items()}
        if isinstance(value, set):
            return sorted(Stats._sanitize_for_json(v) for v in value)
        if isinstance(value, tuple):
            return [Stats._sanitize_for_json(v) for v in value]
        if isinstance(value, list):
            return [Stats._sanitize_for_json(v) for v in value]
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        return str(value)

    def __str__(self):
        return pprint.pformat(self.get_stats(), indent=2)

    def get_requirement_text_stats(self, req_text: str) -> tuple[int | None, int | None, int | None]:
        if req_text:
            cleaned_text = req_text.strip()
            if cleaned_text and cleaned_text[-1] not in '.!?':
                cleaned_text += '.'
            char_count = len(cleaned_text)
            word_count = len(cleaned_text.split())
            sentence_count = len(re.findall(r'[.!?]+(?:\s|$)', cleaned_text))
            return char_count, word_count, sentence_count
        else:
            return None, None, None
