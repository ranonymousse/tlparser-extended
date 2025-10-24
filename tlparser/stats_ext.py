"""Helpers for extended statistics based on Spot tooling."""

from __future__ import annotations

import re
from typing import Any, List


class SpotAnalyzer:
    """Lazily perform Spot-powered analysis and collect diagnostics."""

    def __init__(self, *, verbose: bool = False) -> None:
        self._available: bool | None = None
        self._diagnostics: List[str] = []
        self._classify = None
        self._verbose = verbose
        self._issue_map: dict[str, set[str]] = {}
        self._token_patterns = (
            (re.compile(r"-->", re.IGNORECASE), "->"),
            (re.compile(r"\bnot\b", re.IGNORECASE), "!"),
            (re.compile(r"\band\b", re.IGNORECASE), "&"),
            (re.compile(r"\bor\b", re.IGNORECASE), "|"),
        )

    @property
    def diagnostics(self) -> List[str]:
        """Return accumulated warnings without exposing internal storage."""
        return list(self._diagnostics)

    def issue_entries(self) -> List[tuple[str, List[str]]]:
        """Return sorted (formula, issues[]) pairs for downstream formatting."""
        return [
            (formula, sorted(self._issue_map[formula]))
            for formula in sorted(self._issue_map)
        ]

    def _record_warning(self, message: str) -> None:
        if message not in self._diagnostics:
            self._diagnostics.append(message)

    def _ensure_initialized(self) -> bool:
        if self._available is not None:
            return self._available

        try:
            from tlparser import (
                spot_tools,
            )  # Local import to avoid mandatory dependency
        except Exception as exc:  # pragma: no cover - environment dependent
            self._record_warning(
                "[tlparser] Spot extensions unavailable (spot_tools import failed); "
                f"extended digest columns will be empty. Details: {exc}"
            )
            self._available = False
            return False

        classify_func = getattr(spot_tools, "classify_ltl_property", None)
        spot_status_fn = getattr(spot_tools, "spot_status", None)

        if classify_func is None or spot_status_fn is None:
            self._record_warning(
                "[tlparser] Spot extensions unavailable (missing Spot helper functions); "
                "extended digest columns will be empty."
            )
            self._available = False
            return False

        status_map = spot_status_fn()
        missing = [name for name, info in status_map.items() if not info.get("path")]

        if missing:
            missing_str = ", ".join(sorted(set(missing)))
            self._record_warning(
                "[tlparser] Spot CLI tools not found (missing: "
                f"{missing_str}); extended digest columns will be empty."
            )
            self._available = False
            return False

        self._classify = classify_func
        self._available = True
        return True

    def classify(self, formula: str) -> dict[str, Any] | None:
        """Return Spot-derived statistics for the given formula if possible."""
        if not formula:
            return None

        if not self._ensure_initialized():
            return None

        assert self._classify is not None  # For type checkers
        spot_formula = self._to_spot_syntax(formula)
        try:
            result = self._classify(spot_formula, verbose=self._verbose)
            if isinstance(result, dict):
                original_spot = result.get("formula", spot_formula)
                result["spot_formula"] = original_spot
                result["formula"] = formula
                self._record_partial_warning(formula, result)
            return result
        except FileNotFoundError:
            self._record_warning(
                "[tlparser] Required Spot CLI tool missing during classification; "
                "extended digest columns will be empty."
            )
            self._available = False
        except Exception as exc:  # pragma: no cover - external tool behaviour
            self._record_warning(
                f"[tlparser] Spot classification failed for '{formula}': {exc}; "
                "extended digest columns will be empty for this formula."
            )
        return None

    def _to_spot_syntax(self, formula: str) -> str:
        """Translate friendly syntax (not/and/or/-->) to Spot-compatible operators."""
        translated = formula
        for pattern, replacement in self._token_patterns:
            translated = pattern.sub(replacement, translated)

        # Collapse whitespace after unary negation to avoid '! p' forms Spot dislikes
        translated = re.sub(r"!\s+", "!", translated)

        # Normalise spacing around binary operators for readability
        translated = re.sub(r"\s*(&|\||->)\s*", r" \1 ", translated)
        translated = re.sub(r"\s+", " ", translated).strip()
        return translated

    def _record_partial_warning(self, formula: str, result: dict[str, Any]) -> None:
        issues: list[str] = []

        if result.get("syntactic_safety") == "Error":
            issues.append("syntactic_safety")
        if result.get("is_stutter_invariant_formula") == "Error":
            issues.append("stutter_invariance")
        manna = result.get("manna_pnueli_class")
        if isinstance(manna, str) and manna.lower().startswith("error"):
            issues.append("manna_pnueli_class")

        def _scan_analysis(label: str) -> None:
            data = result.get(label, {})
            if not isinstance(data, dict):
                issues.append(label)
                return
            if data.get("analysis_error"):
                issues.append(f"{label} ({data['analysis_error']})")
                return
            if any(value == "Error" for value in data.values()):
                issues.append(label)

        _scan_analysis("tgba_analysis")
        _scan_analysis("buchi_analysis")

        det = result.get("deterministic_attempt", {})
        if det.get("success") is False:
            err = det.get("error")
            if err:
                issues.append(f"deterministic_attempt ({err})")
            else:
                issues.append("deterministic_attempt")
        else:
            det_data = det.get("automaton_analysis", {})
            if isinstance(det_data, dict) and any(
                value == "Error" for value in det_data.values()
            ):
                issues.append("deterministic_attempt")

        if issues:
            entries = self._issue_map.setdefault(formula, set())
            entries.update(issues)
