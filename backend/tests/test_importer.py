"""
test_importer.py
================
測試 parse_student_data 的 JSON 解析邏輯（不需要 DB）。

覆蓋重點：
- 學生基本資料（學號、系所、入學年）是否正確抽取
- requiredOrElectiveCourse → required_or_elective 的對應
- 體育課（002開頭 / 含「體育」字樣）的 course_type 識別
- 通識 ge_label 推斷（中文通/外文通/書院通/人文通/社科通/自然通/資訊通/核心）
- 群修（remark 為空但 requiredOrElectiveCourse='群'）→ course_type='群修'
- 必修 → course_type='必修'
- score 欄位原樣保留（成績字串、「通過」、「成績未到或無成績」、「停修」）
"""

from __future__ import annotations

import pytest

from src.services.importer import infer_ge_label, parse_student_data

# ──────────────────────────────────────────────
# 輔助：最小 JSON 結構
# ──────────────────────────────────────────────

def _make_json(
    student_number: str = "112703001",
    register_major: str = "資訊科學系",
    register_double_major: str | None = None,
    minor1: str | None = None,
    minor2: str | None = None,
    chinese_name: str = "測試生",
    records: list[dict] | None = None,
) -> list[dict]:
    """製作最小 exportStudentData.json 結構。"""
    grade_records = []
    if records:
        grade_records = [{"AcademicYear": "112", "GradeRecords": records}]
    return [
        {
            "課業學習": {
                "aboutMe": {
                    "studentNumber": student_number,
                    "registerMajor": register_major,
                    "registerDoubleMajor": register_double_major or "",
                    "minor1": minor1 or "",
                    "minor2": minor2 or "",
                    "chineseName": chinese_name,
                },
                "gradeRecordList": grade_records,
            }
        }
    ]


def _rec(
    code: str,
    name: str,
    req: str = "選",
    score: str = "80",
    credit: str = "3.0",
    remark: str = "",
    academic_year: str = "112",
    semester: str = "1",
) -> dict:
    return {
        "courseCode": code,
        "courseName": name,
        "requiredOrElectiveCourse": req,
        "score": score,
        "credit": credit,
        "remark": remark,
        "academicYear": academic_year,
        "semester": semester,
    }


# ──────────────────────────────────────────────
# 1. 學生基本資料解析
# ──────────────────────────────────────────────

class TestStudentInfoParsing:
    def test_student_id_extracted(self):
        data = _make_json(student_number="112703043")
        result = parse_student_data(data)
        assert result["student_info"]["student_id"] == "112703043"

    def test_admission_year_from_student_number(self):
        """入學年由學號前3碼推算。"""
        data = _make_json(student_number="112703043")
        result = parse_student_data(data)
        assert result["student_info"]["admission_year"] == 112

    def test_register_major(self):
        data = _make_json(register_major="資訊科學系")
        result = parse_student_data(data)
        assert result["student_info"]["register_major"] == "資訊科學系"

    def test_double_major_parsed(self):
        data = _make_json(register_double_major="人工智慧應用學士學位學程")
        result = parse_student_data(data)
        assert result["student_info"]["register_double_major"] == "人工智慧應用學士學位學程"

    def test_double_major_empty_string_becomes_none(self):
        data = _make_json(register_double_major="")
        result = parse_student_data(data)
        assert result["student_info"]["register_double_major"] is None

    def test_minor_parsed(self):
        data = _make_json(minor1="統計學系", minor2="")
        result = parse_student_data(data)
        assert result["student_info"]["minor1"] == "統計學系"
        assert result["student_info"]["minor2"] is None

    def test_chinese_name(self):
        data = _make_json(chinese_name="彭啟則")
        result = parse_student_data(data)
        assert result["student_info"]["name"] == "彭啟則"

    def test_list_input_format(self):
        """parse_student_data 接受 list（exportStudentData.json 原始格式）。"""
        data = _make_json(student_number="112703099")
        result = parse_student_data(data)
        assert result["student_info"]["student_id"] == "112703099"

    def test_dict_with_data_key_format(self):
        """也接受 {"data": [...]} 格式。"""
        inner = _make_json(student_number="112703099")
        result = parse_student_data({"data": inner})
        assert result["student_info"]["student_id"] == "112703099"


# ──────────────────────────────────────────────
# 2. 課程 required_or_elective 對應
# ──────────────────────────────────────────────

class TestRequiredOrElectiveMapping:
    def test_bi_maps_to_bi(self):
        data = _make_json(records=[_rec("703049001", "計算機程式設計（一）", req="必")])
        courses = parse_student_data(data)["courses"]
        assert courses[0]["required_or_elective"] == "必"

    def test_qun_maps_to_qun(self):
        data = _make_json(records=[_rec("703044021", "資訊專題（A）", req="群")])
        courses = parse_student_data(data)["courses"]
        assert courses[0]["required_or_elective"] == "群"

    def test_xuan_maps_to_xuan(self):
        data = _make_json(records=[_rec("703834001", "自然語言處理", req="選")])
        courses = parse_student_data(data)["courses"]
        assert courses[0]["required_or_elective"] == "選"

    def test_unknown_req_defaults_to_xuan(self):
        data = _make_json(records=[_rec("999001001", "未知課", req="???")])
        courses = parse_student_data(data)["courses"]
        assert courses[0]["required_or_elective"] == "選"


# ──────────────────────────────────────────────
# 3. course_type 分類
# ──────────────────────────────────────────────

class TestCourseType:
    def test_pe_by_code_prefix_002(self):
        """002 開頭的課是體育。"""
        data = _make_json(records=[_rec("002301041", "體育[男女合班]—網球初級", req="必")])
        courses = parse_student_data(data)["courses"]
        assert courses[0]["course_type"] == "體育"

    def test_pe_by_name_containing_tiyü(self):
        """課名含「體育」也算體育（即使 code 不是 002）。"""
        data = _make_json(records=[_rec("099000001", "體育專項訓練", req="必")])
        courses = parse_student_data(data)["courses"]
        assert courses[0]["course_type"] == "體育"

    def test_ge_course_type_by_ge_label(self):
        """有 ge_label 的課（remark 含通識關鍵字）→ course_type='通識'。"""
        data = _make_json(records=[_rec("041095001", "客家語言與文化", req="群", remark="人文通")])
        courses = parse_student_data(data)["courses"]
        assert courses[0]["course_type"] == "通識"

    def test_required_major_course_type(self):
        """必修且無 ge_label → course_type='必修'。"""
        data = _make_json(records=[_rec("703049001", "計算機程式設計（一）", req="必", remark="")])
        courses = parse_student_data(data)["courses"]
        assert courses[0]["course_type"] == "必修"

    def test_group_elective_course_type(self):
        """群修且無 ge_label → course_type='群修'。"""
        data = _make_json(records=[_rec("703044021", "資訊專題（A）", req="群", remark="")])
        courses = parse_student_data(data)["courses"]
        assert courses[0]["course_type"] == "群修"

    def test_elective_course_type(self):
        data = _make_json(records=[_rec("703834001", "自然語言處理", req="選")])
        courses = parse_student_data(data)["courses"]
        assert courses[0]["course_type"] == "選修"


# ──────────────────────────────────────────────
# 4. ge_label 推斷（infer_ge_label）
# ──────────────────────────────────────────────

class TestInferGeLabel:
    """
    ge_label bits（從高到低）：
    GE_CORE=128, GE_HUMAN=64, GE_SOCIAL=32, GE_NATURAL=16,
    GE_INFO=8,   GE_COLLEGE=4, GE_FOREIGN=2, GE_CHINESE=1
    """

    def test_031_prefix_is_chinese(self):
        label = infer_ge_label("031004061", "國文－古典詩選讀", None)
        assert label & 1  # GE_CHINESE

    def test_032_prefix_is_foreign(self):
        label = infer_ge_label("032002491", "大學英文（二）", None)
        assert label & 2  # GE_FOREIGN

    def test_daxue_yingwen_by_name(self):
        label = infer_ge_label("032001071", "大學英文（一）", "外文通")
        assert label & 2

    def test_045_prefix_is_college(self):
        label = infer_ge_label("045001001", "書院課程", None)
        assert label & 4  # GE_COLLEGE

    def test_remark_renwen_tong(self):
        label = infer_ge_label("999001001", "文化課", "人文通")
        assert label & 64  # GE_HUMAN

    def test_remark_shehui_tong(self):
        label = infer_ge_label("999001001", "社會課", "社會通")
        assert label & 32  # GE_SOCIAL

    def test_remark_ziran_tong(self):
        label = infer_ge_label("042001001", "物理課", "自然通")
        assert label & 16  # GE_NATURAL

    def test_remark_zixun_tong(self):
        label = infer_ge_label("999001001", "資訊課", "資訊通")
        assert label & 8  # GE_INFO

    def test_remark_hexin(self):
        """含「核心」→ 加上 GE_CORE bit。"""
        label = infer_ge_label("999001001", "哲學概論", "人文通 核心")
        assert label & 128  # GE_CORE
        assert label & 64   # GE_HUMAN

    def test_no_ge_label_for_plain_elective(self):
        label = infer_ge_label("703834001", "自然語言處理", None)
        assert label == 0

    def test_remark_shu_yuan_tong(self):
        label = infer_ge_label("045010001", "書院導師課", "書院通")
        assert label & 4  # GE_COLLEGE


# ──────────────────────────────────────────────
# 5. score 保留原始字串
# ──────────────────────────────────────────────

class TestScoreParsing:
    def test_numeric_score_preserved_as_string(self):
        data = _make_json(records=[_rec("703049001", "程式設計", score="85.5")])
        courses = parse_student_data(data)["courses"]
        assert courses[0]["score"] == "85.5"

    def test_tonguo_preserved(self):
        data = _make_json(records=[_rec("703056001", "程式能力檢定", score="通過")])
        courses = parse_student_data(data)["courses"]
        assert courses[0]["score"] == "通過"

    def test_in_progress_score_preserved(self):
        data = _make_json(records=[_rec("703044021", "資訊專題", score="成績未到或無成績")])
        courses = parse_student_data(data)["courses"]
        assert courses[0]["score"] == "成績未到或無成績"

    def test_tingxiu_preserved(self):
        data = _make_json(records=[_rec("703901001", "機器學習概論", score="停修")])
        courses = parse_student_data(data)["courses"]
        assert courses[0]["score"] == "停修"


# ──────────────────────────────────────────────
# 6. 多學年、多筆課程 → 全部被解析
# ──────────────────────────────────────────────

class TestMultipleCoursesAndYears:
    def test_courses_from_multiple_year_blocks(self):
        data = [
            {
                "課業學習": {
                    "aboutMe": {
                        "studentNumber": "112703001",
                        "registerMajor": "資訊科學系",
                        "registerDoubleMajor": "",
                        "minor1": "",
                        "minor2": "",
                        "chineseName": "測試生",
                    },
                    "gradeRecordList": [
                        {
                            "AcademicYear": "112",
                            "GradeRecords": [
                                _rec("703049001", "計算機程式設計（一）", req="必", score="98"),
                                _rec("703002001", "線性代數", req="必", score="90"),
                            ],
                        },
                        {
                            "AcademicYear": "113",
                            "GradeRecords": [
                                _rec("703008001", "資料結構", req="必", score="84", academic_year="113"),
                                _rec("703038001", "人工智慧概論", req="群", score="88", academic_year="113"),
                            ],
                        },
                    ],
                }
            }
        ]
        result = parse_student_data(data)
        assert len(result["courses"]) == 4
        codes = [c["course_code"] for c in result["courses"]]
        assert "703049001" in codes
        assert "703038001" in codes

    def test_empty_grade_records_yields_no_courses(self):
        data = _make_json(records=[])
        result = parse_student_data(data)
        assert result["courses"] == []


class TestWaivedCourseList:
    """waivedCourseList（免修課）應被解析為 score='通過' 的課程。"""

    def _make_waived_json(self, waived_records):
        return [{
            "課業學習": {
                "aboutMe": {
                    "studentNumber": "112703001",
                    "registerMajor": "資訊科學系",
                    "registerDoubleMajor": "",
                    "minor1": "", "minor2": "",
                    "chineseName": "測試生",
                },
                "gradeRecordList": [],
                "waivedCourseList": waived_records,
            }
        }]

    def test_waived_course_score_is_passed(self):
        """免修課的 score 必須是「通過」。"""
        data = self._make_waived_json([{
            "courseCode": "032001001",
            "courseName": "大學英文（一）",
            "credit": "3.0",
            "requiredOrElectiveCourse": "必",
            "academicYear": "110",
            "semester": "1",
        }])
        courses = parse_student_data(data)["courses"]
        assert len(courses) == 1
        assert courses[0]["score"] == "通過"
        assert courses[0]["course_code"] == "032001001"
        assert courses[0]["credit"] == 3.0

    def test_waived_course_counted_in_credits(self):
        """免修課的學分應被計入（score=通過 → is_passed=True）。"""
        from src.services.importer import is_passed
        assert is_passed("通過") is True

    def test_empty_waived_list_no_extra_courses(self):
        """waivedCourseList 為空時不新增任何課程。"""
        data = self._make_waived_json([])
        courses = parse_student_data(data)["courses"]
        assert courses == []

    def test_waived_course_with_no_code_or_name_skipped(self):
        """courseCode 和 courseName 都是空的免修記錄應被跳過。"""
        data = self._make_waived_json([{
            "courseCode": "",
            "courseName": "",
            "credit": "3.0",
        }])
        courses = parse_student_data(data)["courses"]
        assert courses == []

    def test_waived_and_grade_courses_combined(self):
        """gradeRecordList 和 waivedCourseList 的課程應合併。"""
        raw = [{
            "課業學習": {
                "aboutMe": {
                    "studentNumber": "112703001",
                    "registerMajor": "資訊科學系",
                    "registerDoubleMajor": "",
                    "minor1": "", "minor2": "",
                    "chineseName": "測試生",
                },
                "gradeRecordList": [{"AcademicYear": "112", "GradeRecords": [
                    {"courseCode": "703049001", "courseName": "計算機程式設計（一）",
                     "requiredOrElectiveCourse": "必", "score": "90",
                     "credit": "3.0", "remark": "", "academicYear": "112", "semester": "1"},
                ]}],
                "waivedCourseList": [
                    {"courseCode": "032001001", "courseName": "大學英文（一）",
                     "credit": "3.0", "requiredOrElectiveCourse": "必",
                     "academicYear": "110", "semester": "1"},
                ],
            }
        }]
        courses = parse_student_data(raw)["courses"]
        assert len(courses) == 2
        codes = [c["course_code"] for c in courses]
        assert "703049001" in codes
        assert "032001001" in codes
        waived = next(c for c in courses if c["course_code"] == "032001001")
        assert waived["score"] == "通過"
