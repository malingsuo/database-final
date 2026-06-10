from types import SimpleNamespace

from src.services.checker import _build_sc_by_code, _match_courses_from_rules


def _course(code: str, semester: int) -> SimpleNamespace:
    return SimpleNamespace(
        course_code=code,
        course_name="微積分甲",
        credit=3,
        score="80",
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

    passed, _, missing, earned, _, _, req_earned, _, req_missing = _match_courses_from_rules(
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
