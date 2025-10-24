# Build an install spot from https://spot.lre.epita.fr/install.html
# We are assuming spot 2.13.1


import sys
import subprocess
import json
import shutil
import os

SHOW_INVOCATIONS = False  # Set to True to print each command invoked to stderr

REQUIRED_SPOT_TOOLS = ("ltl2tgba", "ltlfilt", "autfilt")

_VERBOSE = False


def set_verbose(enabled: bool) -> None:
    global _VERBOSE
    _VERBOSE = bool(enabled)


def get_verbose() -> bool:
    return _VERBOSE


def _debug(message: str) -> None:
    if _VERBOSE:
        print(message, file=sys.stderr)


def _which_all(names: list[str] | tuple[str, ...]) -> dict[str, str | None]:
    return {name: shutil.which(name) for name in names}


def spot_status() -> dict:
    """Return availability and versions for Spot CLI tools.
    Keys: tool name; values: {"path": str|None, "version": str|None}
    """
    status: dict[str, dict[str, str | None]] = {}
    for exe, path in _which_all(REQUIRED_SPOT_TOOLS).items():
        info: dict[str, str | None] = {"path": path, "version": None}
        if path:
            try:
                # Prefer stdout, fall back to stderr
                p = subprocess.run([exe, "--version"], text=True, capture_output=True)
                ver = (p.stdout or p.stderr).strip() or None
                info["version"] = ver
            except Exception:
                # Don't fail status collection on odd version output
                pass
        status[exe] = info
    return status


def print_spot_status() -> int:
    """Print a human-friendly status and return 0 if all required tools exist, else 1."""
    st = spot_status()
    missing = [k for k, v in st.items() if not v.get("path")]
    print("[tlparser] Spot tool availability:\n", file=sys.stderr)
    for k, v in st.items():
        path = v.get("path") or "NOT FOUND"
        ver = v.get("version") or "?"
        print(f"  - {k:9s} : {path}    (version: {ver})", file=sys.stderr)
    if missing:
        print("\n[tlparser] Spot seems partially or fully missing.", file=sys.stderr)
        print(
            "Install suggestions: conda-forge 'spot' or your distro packages providing ltl2tgba/ltlfilt/autfilt.",
            file=sys.stderr,
        )
        return 1
    return 0


def require_spot(tools: tuple[str, ...] = REQUIRED_SPOT_TOOLS) -> bool:
    """Return True if all given tools are available; print a single warning otherwise."""
    found = _which_all(tools)
    missing = [k for k, v in found.items() if v is None]
    if missing:
        print(
            "[tlparser] Warning: Spot is not fully available; missing: "
            + ", ".join(missing)
            + ". Some results will be skipped or approximated.",
            file=sys.stderr,
        )
        return False
    return True


def invoke(command, input_data=None):
    cmd_str = " ".join(command)
    if SHOW_INVOCATIONS:
        if input_data:
            input_snippet = input_data[:100].replace("\n", "\\n") + (
                "..." if len(input_data) > 100 else ""
            )
            print(
                f"\nInvoking command: {cmd_str} (piping input: '{input_snippet}')",
                file=sys.stderr,
            )
        else:
            print(f"\nInvoking command: {cmd_str}", file=sys.stderr)
    try:
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE if input_data else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )
        stdout, stderr = process.communicate(input=input_data)
    except FileNotFoundError as e:
        # Nicer message for missing Spot tools
        missing = command[0]
        raise FileNotFoundError(
            f"Required tool '{missing}' not found in PATH. Install Spot CLI tools (ltl2tgba/ltlfilt/autfilt)."
        ) from e

    if process.returncode != 0:
        is_filter_no_match = (
            command[0] == "ltlfilt"
            and process.returncode == 1
            and "--format=" not in cmd_str
        ) or (command[0] == "autfilt" and process.returncode == 1)
        if is_filter_no_match and not stderr and not stdout:
            return ""

        error_msg = f"Command '{' '.join(command)}' returned non-zero exit status {process.returncode}."
        if stderr:
            error_msg += f"\nStderr: {stderr.strip()}"
        if stdout:
            error_msg += f"\nStdout: {stdout.strip()}"
        raise subprocess.CalledProcessError(
            process.returncode, command, output=stdout, stderr=stderr
        )
    return stdout.strip()


def get_automaton_and_stats(ltl_formula, to_buchi=False, to_deterministic=False):
    """
    Translates LTL and attempts to get basic automaton statistics directly from ltl2tgba
    Returns: (hoa_automaton_string, stats_dict)
    """
    require_spot(("ltl2tgba",))
    cmd_base = ["ltl2tgba", "-f", ltl_formula]
    cmd_stats = ["ltl2tgba", "-f", ltl_formula]

    if to_buchi:
        cmd_base.append("-B")
        cmd_stats.append("-B")
    if to_deterministic:
        cmd_base.append("-D")
        cmd_stats.append("-D")

    hoa_automaton = ""
    try:
        hoa_automaton = invoke(cmd_base)
    except subprocess.CalledProcessError as e:
        _debug(f"Error generating automaton: {e}")
        return "", {"error": str(e)}

    stats_dict = {}
    try:
        stats_output = invoke(cmd_stats + ["--stats=%s %t %p %d %a"])
        parts = stats_output.split()
        if len(parts) == 5:
            stats_dict["state_count"] = int(parts[0])
            stats_dict["transition_count"] = int(parts[1])
            stats_dict["is_complete"] = parts[2] == "1"
            stats_dict["is_deterministic"] = parts[3] == "1"
            stats_dict["acceptance_sets"] = int(parts[4])
            stats_dict["analysis_source"] = "ltl2tgba_stats"
        else:
            stats_dict["error"] = "Unexpected stats output format from ltl2tgba."
    except (subprocess.CalledProcessError, ValueError) as e:
        stats_dict["error"] = f"Failed to get direct stats from ltl2tgba: {e}"

    return hoa_automaton, stats_dict


def analyze_automaton_fallback(hoa_automaton):
    """
    Analyzes an automaton for properties using autfilt.
    Do property checks, return the full HOA string on match
    """
    results = {}
    if not hoa_automaton.strip():
        return {
            "is_deterministic": "Error",
            "is_complete": "Error",
            "state_count": "Error",
            "transition_count": "Error",
            "acceptance_sets": "Error",
            "is_stutter_invariant": "Error",
            "analysis_error": "Empty or malformed HOA input for autfilt fallback",
        }

    def get_stat_int(stat_flag):
        try:
            output = invoke(
                ["autfilt", f"--stats={stat_flag}"], input_data=hoa_automaton
            )
            return int(output)
        except (subprocess.CalledProcessError, ValueError):
            return "Error"
        except FileNotFoundError:
            return "Error"

    def check_property_by_output(prop_flag):
        try:
            output = invoke(["autfilt", prop_flag], input_data=hoa_automaton)
            return bool(output)
        except subprocess.CalledProcessError:
            return "Error"
        except FileNotFoundError:
            return "Error"

    results["is_deterministic"] = check_property_by_output("--is-deterministic")
    results["is_complete"] = check_property_by_output("--is-complete")
    results["is_stutter_invariant"] = check_property_by_output("--is-stutter-invariant")

    results["state_count"] = get_stat_int("s")
    results["transition_count"] = get_stat_int("t")
    results["acceptance_sets"] = get_stat_int("c")

    results["analysis_source"] = "autfilt_fallback"
    return results


def check_ltl_property_type(ltl_formula, check_type="syntactic_safety"):
    """
    Check LTL formula properties using ltlfilt
    Args:
        ltl_formula (str): The LTL formula
        check_type (str): 'syntactic_safety' or 'stutter_invariant'
    Returns:
        bool: True if it matches, False otherwise
        str: "Error" if the command failed
    """
    option_map = {
        "syntactic_safety": "--syntactic-safety",
        "stutter_invariant": "--stutter-invariant",
    }
    flag = option_map.get(check_type)
    if not flag:
        raise ValueError(f"Unknown check_type: {check_type}")

    _debug(
        f"Checking if LTL '{ltl_formula}' is {check_type.replace('_', ' ')} using {flag}..."
    )
    try:
        output = invoke(["ltlfilt", "-f", ltl_formula, flag])
        return len(output) > 0
    except subprocess.CalledProcessError as e:
        _debug(
            f"Error checking {check_type.replace('_', ' ')} for '{ltl_formula}'. Stderr: {e.stderr.strip()}"
        )
        return "Error"
    except FileNotFoundError:
        print(
            f"Error: ltlfilt command not found. Make sure Spot tools are in your PATH.",
            file=sys.stderr,
        )
        return "Error"
    except Exception as e:
        _debug(
            f"An unexpected error occurred during {check_type.replace('_', ' ')} check: {e}"
        )
        return "Error"


def get_manna_pnueli_class(ltl_formula):
    """
    Get Manna-Pnueli hierarchy class of an LTL formula using ltlfilt.
    Return: str: The class name(s) (e.g., "Safety", "Liveness, Guarantee"), or "Error" on failure.
    """
    _debug(f"Determining Manna-Pnueli class for '{ltl_formula}' using %[vw]h...")
    try:
        output = invoke(["ltlfilt", "-f", ltl_formula, "--format=%[vw]h"])
        result = output.strip()
        if not result or result.startswith("%["):
            return "Unclassified/Error (Format Issue)"
        return result
    except subprocess.CalledProcessError as e:
        _debug(
            f"Error determining Manna-Pnueli class for '{ltl_formula}'. Stderr: {e.stderr.strip()}"
        )
        return "Error"
    except FileNotFoundError:
        print(
            f"Error: ltlfilt command not found. Make sure Spot tools are in your PATH.",
            file=sys.stderr,
        )
        return "Error"
    except Exception as e:
        _debug(
            f"An unexpected error occurred during Manna-Pnueli class check: {e}"
        )
        return "Error"


def classify_ltl_property(ltl_formula, *, verbose: bool | None = None):
    prev_verbose = get_verbose()
    if verbose is not None:
        set_verbose(verbose)

    try:
        classification = {
            "formula": ltl_formula,
            "syntactic_safety": None,
            "is_stutter_invariant_formula": None,
            "manna_pnueli_class": "Unknown",
            "tgba_analysis": {},
            "buchi_analysis": {},
            "deterministic_attempt": {"success": None, "automaton_analysis": {}},
        }

        # Check syntactic safety
        classification["syntactic_safety"] = check_ltl_property_type(
            ltl_formula, "syntactic_safety"
        )

        # Check stutter invariance
        classification["is_stutter_invariant_formula"] = check_ltl_property_type(
            ltl_formula, "stutter_invariant"
        )

        # Get Manna-Pnueli Class
        classification["manna_pnueli_class"] = get_manna_pnueli_class(ltl_formula)

        # Translate to default TGBA and analyze
        hoa_tgba, tgba_stats = get_automaton_and_stats(
            ltl_formula, to_buchi=False, to_deterministic=False
        )
        if "error" in tgba_stats:
            _debug(f"Falling back to autfilt for TGBA analysis: {tgba_stats['error']}")
            classification["tgba_analysis"] = analyze_automaton_fallback(hoa_tgba)
        else:
            classification["tgba_analysis"] = tgba_stats
            tgba_automaton_stutter_check = analyze_automaton_fallback(hoa_tgba).get(
                "is_stutter_invariant"
            )
            classification["tgba_analysis"]["is_stutter_invariant"] = (
                tgba_automaton_stutter_check
            )

        # Translate to Buchi (if possible) and analyze
        hoa_buchi, buchi_stats = get_automaton_and_stats(
            ltl_formula, to_buchi=True, to_deterministic=False
        )
        if "error" in buchi_stats:
            _debug(f"Falling back to autfilt for Buchi analysis: {buchi_stats['error']}")
            classification["buchi_analysis"] = analyze_automaton_fallback(hoa_buchi)
        else:
            classification["buchi_analysis"] = buchi_stats
            buchi_automaton_stutter_check = analyze_automaton_fallback(hoa_buchi).get(
                "is_stutter_invariant"
            )
            classification["buchi_analysis"]["is_stutter_invariant"] = (
                buchi_automaton_stutter_check
            )

        # Attempt to produce a deterministic automaton and analyze
        hoa_deterministic, deterministic_stats = get_automaton_and_stats(
            ltl_formula, to_buchi=False, to_deterministic=True
        )

        if "error" in deterministic_stats:
            classification["deterministic_attempt"]["success"] = False
            classification["deterministic_attempt"]["error"] = deterministic_stats["error"]
        else:
            classification["deterministic_attempt"]["success"] = True
            classification["deterministic_attempt"][
                "automaton_analysis"
            ] = deterministic_stats
            det_automaton_stutter_check = analyze_automaton_fallback(hoa_deterministic).get(
                "is_stutter_invariant"
            )
            classification["deterministic_attempt"]["automaton_analysis"][
                "is_stutter_invariant"
            ] = det_automaton_stutter_check

        return classification
    finally:
        if verbose is not None:
            set_verbose(prev_verbose)


if __name__ == "__main__":
    # Lightweight CLI: `python spot_tools.py --check-spot` prints availability and exits non-zero if missing
    if "--check-spot" in sys.argv or os.environ.get("TLPARSER_SPOT_CHECK") == "1":
        code = print_spot_status()
        sys.exit(code)

    verbose_flag = False
    formulas: list[str] = []
    for arg in sys.argv[1:]:
        if arg in {"--verbose", "-v"}:
            verbose_flag = True
        elif arg.startswith("--"):
            continue
        else:
            formulas.append(arg)
    if not formulas:
        print(
            "Provide one or more LTL formulas as arguments, or use --check-spot to inspect availability.",
            file=sys.stderr,
        )
        sys.exit(1)

    for formula_str in formulas:
        try:
            classification = classify_ltl_property(formula_str, verbose=verbose_flag)
        except Exception as exc:
            print(
                f"[tlparser] Failed to classify '{formula_str}': {exc}", file=sys.stderr
            )
            continue

        print(json.dumps(classification, indent=2))
