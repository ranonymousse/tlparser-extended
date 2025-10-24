class TestCaseData:
    __test__ = False
    def __init__(self, f_code='', asth='', aps=0, cops=0, lops=0, tops=0, entropy_lops_tops=None):
        self.f_code = f_code
        self.asth = asth
        self.aps = aps
        self.cops = cops
        self.lops = lops
        self.tops = tops
        self.entropy_lops_tops = entropy_lops_tops


class TestCaseDataExt(TestCaseData):
    __test__ = False

    def __init__(
        self,
        f_code: str = '',
        asth: int | str = '',
        aps: int = 0,
        cops: int = 0,
        lops: int = 0,
        tops: int = 0,
        entropy_lops_tops=None,
        *,
        syntactic_safety=None,
        is_stutter_invariant_formula=None,
        manna_pnueli_class=None,
        tgba_state_count=None,
        tgba_transition_count=None,
        tgba_is_complete=None,
        tgba_is_deterministic=None,
        tgba_acceptance_sets=None,
        tgba_is_stutter_invariant=None,
        buchi_state_count=None,
        buchi_transition_count=None,
        buchi_is_complete=None,
        buchi_is_deterministic=None,
        buchi_acceptance_sets=None,
        buchi_is_stutter_invariant=None,
        det_attempt_success=None,
        det_attempt_error=None,
        manna_pnueli_class_contains=None,
        det_state_count=None,
        det_transition_count=None,
        det_is_complete=None,
        det_is_deterministic=None,
        det_acceptance_sets=None,
        det_is_stutter_invariant=None,
    ):
        super().__init__(
            f_code,
            asth,
            aps,
            cops,
            lops,
            tops,
            entropy_lops_tops,
        )
        self.syntactic_safety = syntactic_safety
        self.is_stutter_invariant_formula = is_stutter_invariant_formula
        self.manna_pnueli_class = manna_pnueli_class
        self.tgba_state_count = tgba_state_count
        self.tgba_transition_count = tgba_transition_count
        self.tgba_is_complete = tgba_is_complete
        self.tgba_is_deterministic = tgba_is_deterministic
        self.tgba_acceptance_sets = tgba_acceptance_sets
        self.tgba_is_stutter_invariant = tgba_is_stutter_invariant
        self.buchi_state_count = buchi_state_count
        self.buchi_transition_count = buchi_transition_count
        self.buchi_is_complete = buchi_is_complete
        self.buchi_is_deterministic = buchi_is_deterministic
        self.buchi_acceptance_sets = buchi_acceptance_sets
        self.buchi_is_stutter_invariant = buchi_is_stutter_invariant
        self.det_attempt_success = det_attempt_success
        self.det_attempt_error = det_attempt_error
        self.manna_pnueli_class_contains = manna_pnueli_class_contains
        self.det_state_count = det_state_count
        self.det_transition_count = det_transition_count
        self.det_is_complete = det_is_complete
        self.det_is_deterministic = det_is_deterministic
        self.det_acceptance_sets = det_acceptance_sets
        self.det_is_stutter_invariant = det_is_stutter_invariant
