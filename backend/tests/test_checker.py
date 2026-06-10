from types import SimpleNamespace

from src.services.checker import _build_sc_by_code, _match_courses_from_rules


def _course(code: str, semester: int, score: str = "80", credit: int = 3) -> SimpleNamespace:
    return SimpleNamespace(
        course_code=code,
        course_name="微積分甲",
        credit=credit,
        score=score,
        year=112,
        semester=semester,
    )


def test_multi_semester_same_name_courses_are_all_listed() -> None:
    rule_courses = [{
        "name": "微積分甲",
        "type": "必修",
        "credits": 6,
        "semesters": 2,
        "course_code_required": "000713",
    }]
    student_courses = [_course("000713011", 1), _course("000713012", 2)]

    passed, _, missing, earned, _, _, req_earned, _, req_missing, _ = _match_courses_from_rules(
        rule_courses,
        student_courses,
        _build_sc_by_code(student_courses),
    )

    assert [c["course_code"] for c in passed] == ["000713011", "000713012"]
    assert [c["credits"] for c in passed] == [3, 3]
    assert missing == []
    assert earned == 6
    assert req_earned == 6
    assert req_missing == 0


def test_single_semester_rule_still_uses_one_candidate() -> None:
    rule_courses = [{
        "name": "微積分甲",
        "type": "必修",
        "credits": 3,
        "semesters": 1,
        "course_code_required": "000713",
    }]
    student_courses = [_course("000713011", 1), _course("000713012", 2)]

    passed, _, _, earned, *_ = _match_courses_from_rules(
        rule_courses,
        student_courses,
        _build_sc_by_code(student_courses),
    )

    assert [c["course_code"] for c in passed] == ["000713011"]
    assert earned == 3


def test_zero_credit_required_missing_triggers_incomplete() -> None:
    """0 學分必修（如程式能力檢定）缺修時，zero_credit_req_missing 應為 1。
    確保上層 status 判定不誤判為 complete。"""
    rule_courses = [{
        "name": "程式能力檢定",
        "type": "必修",
        "credits": 0,
        "semesters": 1,
        "course_code_required": "703056001",
    }]
    student_courses: list = []  # 完全沒修這門課

    passed, in_progress, missing, earned, _, _, _, _, req_missing, zero_missing = _match_courses_from_rules(
        rule_courses,
        student_courses,
        _build_sc_by_code(student_courses),
    )

    assert passed == []
    assert earned == 0
    assert req_missing == 0        # 學分角度缺口是 0（因為 0 學分課）
    assert zero_missing == 1       # 但 0 學分必修缺修計數應為 1
    assert len(missing) == 1       # 缺修清單裡應有這門課
    assert missing[0]["course_name"] == "程式能力檢定"


def test_zero_credit_required_passed_no_missing() -> None:
    """0 學分必修通過時，zero_credit_req_missing 應為 0。"""
    rule_courses = [{
        "name": "程式能力檢定",
        "type": "必修",
        "credits": 0,
        "semesters": 1,
        "course_code_required": "703056001",
    }]

    passing_course = SimpleNamespace(
        course_code="703056001",
        course_name="程式能力檢定",
        credit=0,
        score="通過",
        year=112,
        semester=1,
    )
    student_courses = [passing_course]

    passed, _, missing, earned, _, _, _, _, req_missing, zero_missing = _match_courses_from_rules(
        rule_courses,
        student_courses,
        _build_sc_by_code(student_courses),
    )

    assert len(passed) == 1
    assert missing == []
    assert req_missing == 0
    assert zero_missing == 0  # 有通過，不應計入缺修


def test_zero_credit_required_failed_triggers_incomplete() -> None:
    """0 學分必修不通過（failed）時，zero_credit_req_missing 也應為 1。"""
    rule_courses = [{
        "name": "程式能力檢定",
        "type": "必修",
        "credits": 0,
        "semesters": 1,
        "course_code_required": "703056001",
    }]

    failed_course = SimpleNamespace(
        course_code="703056001",
        course_name="程式能力檢定",
        credit=0,
        score="停修",  # failed
        year=112,
        semester=1,
    )
    student_courses = [failed_course]

    _, _, missing, _, _, _, _, _, req_missing, zero_missing = _match_courses_from_rules(
        rule_courses,
        student_courses,
        _build_sc_by_code(student_courses),
    )

    assert req_missing == 0   # 學分缺口仍是 0
    assert zero_missing == 1  # 但 0 學分必修不通過，counter 應為 1
    assert any(c.get("note") == "成績不通過" for c in missing)
