"""
test_graduation_integration.py
================================
Integration test：JSON 上傳 → DB 匯入 → 畢業審核全流程，使用真實 PostgreSQL。

前置：docker compose up -d db（test DB: dbfinal_test）

測試情境（資訊科學系 112 入學）：

  StudentA - 完整畢業生
    - 全部必修通過、群A 2門、群B/C/E各1門(通過)、通識齊全、體育4學期

  StudentB - 必修缺漏
    - 缺「演算法」和「作業系統」

  StudentC - 群修不足
    - 必修全過，但群A只1門、群B~E只覆蓋2個領域

  StudentD - 體育不足
    - 必修全過，但體育只修了2學期

  StudentE - in_progress 課程（正在修）
    - 必修幾乎全過，但「演算法」score=成績未到或無成績
    - 確認 in_progress 不算 earned，但進 in_progress_courses

  StudentF - 班次不同的群修（測試前6碼prefix比對）
    - 資訊專題（A）的 code 是 703044021（班21），規則是 703044001（班01）
    - 分散式系統（群E）code 完全吻合

  StudentG - 通識齊全
    - 測試 ge_label 各類別都有、核心通識 ≥2 個領域
"""
from __future__ import annotations

import pytest

from src.services.checker import check_ge, check_graduation, check_major, check_pe
from src.services.importer import import_student_json_from_dict

# ─── 課程代號常數（資科系112，來自graduation_requirements JSON） ────────────

# 必修
CALCULUS    = "000713011"  # 微積分甲(一) prefix 000713
CALCULUS_2  = "000713012"  # 微積分甲(二)
CS1         = "703049001"  # 計算機程式設計（一）
LINEAR_ALG  = "703002001"  # 線性代數
OOP         = "703009001"  # 物件導向程式設計
DS          = "703008001"  # 資料結構
PROB        = "703017001"  # 機率論
DISCRETE    = "703007001"  # 離散數學
CODING_CERT = "703056001"  # 程式能力檢定（0學分）
ALGO        = "703022001"  # 演算法
DSL_LAB     = "703015001"  # 數位系統實驗（0學分）
DSL         = "703014001"  # 數位系統導論
OS          = "703016001"  # 作業系統
COA         = "703019001"  # 計算機結構與組織

ALL_REQUIRED = [
    (CALCULUS,   "微積分甲(一)",      3, "必"),
    (CALCULUS_2, "微積分甲(二)",      3, "必"),
    (CS1,        "計算機程式設計（一）",3, "必"),
    (LINEAR_ALG, "線性代數",          3, "必"),
    (OOP,        "物件導向程式設計",   3, "必"),
    (DS,         "資料結構",          3, "必"),
    (PROB,       "機率論",            3, "必"),
    (DISCRETE,   "離散數學",          3, "必"),
    (CODING_CERT,"程式能力檢定",      0, "必"),
    (ALGO,       "演算法",            3, "必"),
    (DSL_LAB,    "數位系統實驗",      0, "必"),
    (DSL,        "數位系統導論",      3, "必"),
    (OS,         "作業系統",          3, "必"),
    (COA,        "計算機結構與組織",  3, "必"),
]

# 群A（資訊專題）
PROJ_A_021  = "703044021"  # 班21 → prefix 703044 → 比到規則 703044001
PROJ_B      = "703045001"
# 群B
AI_INTRO    = "703038001"  # 人工智慧概論
# 群C
COMP_GRAPH  = "703053001"  # 電腦圖學
# 群D
INFO_SEC    = "703060001"  # 資訊安全
# 群E
DIST_SYS    = "703059001"  # 分散式系統

# 體育
PE1 = "002301001"
PE2 = "002302001"
PE3 = "002303001"
PE4 = "002304001"

# 通識
GE_CHINESE_COURSE  = "031004001"  # 國文（中文通，031開頭）
GE_FOREIGN_1       = "032001001"  # 大學英文（一）（外文通）
GE_FOREIGN_2       = "032002001"  # 大學英文（二）（外文通）
GE_HUMAN_CORE      = "099001001"  # 人文核心通識
GE_HUMAN_2         = "099002001"  # 人文通識
GE_SOCIAL_CORE     = "099003001"  # 社科核心通識
GE_NATURAL         = "099004001"  # 自然通識
GE_COLLEGE         = "045001001"  # 書院通識


# ─── helper：製作最小 JSON ────────────────────────────────────────────────────

def _rec(code, name, req="選", score="80", credit="3.0", remark="",
         academic_year="112", semester="1"):
    return {
        "courseCode": code, "courseName": name,
        "requiredOrElectiveCourse": req, "score": score,
        "credit": credit, "remark": remark,
        "academicYear": academic_year, "semester": semester,
    }


def _make_json(student_number, major="資訊科學系", double_major=None,
               minor1=None, minor2=None, name="測試生", records=None):
    return [{
        "課業學習": {
            "aboutMe": {
                "studentNumber": student_number,
                "registerMajor": major,
                "registerDoubleMajor": double_major or "",
                "minor1": minor1 or "",
                "minor2": minor2 or "",
                "chineseName": name,
            },
            "gradeRecordList": [
                {"AcademicYear": "112", "GradeRecords": records or []}
            ],
        }
    }]


def _import(session, student_number, records, major="資訊科學系",
            double_major=None, minor1=None, minor2=None):
    data = _make_json(student_number, major=major, double_major=double_major,
                      minor1=minor1, minor2=minor2, records=records)
    student, _ = import_student_json_from_dict(session, data)
    return student


def _required_records(exclude_codes=(), in_progress_codes=()):
    """產生全部必修課程的 record list，可以排除或設為 in_progress。"""
    records = []
    for code, name, credit, req in ALL_REQUIRED:
        if code in exclude_codes:
            continue
        score = "成績未到或無成績" if code in in_progress_codes else "80"
        if name == "程式能力檢定":
            score = "通過" if code not in in_progress_codes else "成績未到或無成績"
        records.append(_rec(code, name, req=req, score=score,
                            credit=str(float(credit))))
    return records


def _ge_records():
    """完整通識課程（共30學分 >= 28，各類齊全，有2個核心領域）。

    計算：
      中文通 3 + 外文通 6 + 人文通 6 + 社會通 6 + 自然通 6 + 書院通 3 = 30（cap 到 28）
      資訊通 min=0（資科系免修），各類都達到 min。
    """
    return [
        _rec(GE_CHINESE_COURSE,  "國文",         req="群", score="80", credit="3.0"),           # 中文通 3
        _rec(GE_FOREIGN_1,       "大學英文（一）", req="必", score="80", credit="3.0"),           # 外文通 3
        _rec(GE_FOREIGN_2,       "大學英文（二）", req="必", score="80", credit="3.0"),           # 外文通 6
        _rec(GE_HUMAN_CORE,      "人文核心通識",   req="群", score="80",
             credit="3.0", remark="人文通 核心"),                                                # 人文通 3（核心）
        _rec(GE_HUMAN_2,         "人文通識",       req="群", score="80",
             credit="3.0", remark="人文通"),                                                     # 人文通 6
        _rec(GE_SOCIAL_CORE,     "社科核心通識",   req="群", score="80",
             credit="3.0", remark="社會通 核心"),                                                # 社會通 3（核心）
        _rec(GE_SOCIAL_CORE+"1", "社科通識",       req="群", score="80",
             credit="3.0", remark="社會通"),                                                     # 社會通 6
        _rec(GE_NATURAL,         "自然通識",       req="群", score="80",
             credit="3.0", remark="自然通"),                                                     # 自然通 3
        _rec(GE_NATURAL+"1",     "自然通識（二）",  req="群", score="80",
             credit="3.0", remark="自然通"),                                                     # 自然通 6
        _rec(GE_COLLEGE,         "書院課",         req="群", score="80",
             credit="3.0", remark="書院通"),                                                     # 書院通 3
    ]  # 合計 33，各類 cap 後 = 3+6+7+7+7+0+3 = 33；GE_REQUIRED cap 到 28，各類均 complete


def _pe_records(count=4):
    pe_list = [PE1, PE2, PE3, PE4]
    return [_rec(pe_list[i], f"體育{i+1}", req="必", score="80", credit="1.0")
            for i in range(count)]


# ─── StudentA：完整畢業生 ─────────────────────────────────────────────────────

class TestStudentA_Complete:
    """必修全過、群A 2門、群B/C/E各1門通過、通識齊全、體育4學期 → 全部 complete。"""

    @pytest.fixture(autouse=True)
    def setup(self, db_session):
        records = (
            _required_records()
            + [
                # 群A（注意班次021 → prefix 703044 比到規則 703044001）
                _rec(PROJ_A_021, "資訊專題（A）", req="群", score="88", credit="3.0"),
                _rec(PROJ_B,     "資訊專題（B）", req="群", score="90", credit="3.0"),
                # 群B、C、D、E（需3個不同領域）
                _rec(AI_INTRO,   "人工智慧概論", req="群", score="88", credit="3.0"),
                _rec(COMP_GRAPH, "電腦圖學",     req="群", score="87", credit="3.0"),
                _rec(INFO_SEC,   "資訊安全",     req="群", score="85", credit="3.0"),
                _rec(DIST_SYS,   "分散式系統",   req="群", score="82", credit="3.0"),
            ]
            + _ge_records()
            + _pe_records(4)
        )
        self.student = _import(db_session, "112703901", records)
        self.session = db_session

    def test_major_check_complete(self):
        result = check_major(self.session, self.student, "資訊科學系")
        assert result["status"] == "complete", result["group_violations"]

    def test_major_no_missing_courses(self):
        result = check_major(self.session, self.student, "資訊科學系")
        # 必修不應出現在 missing（必修全部都有修且通過）
        required_missing = [c for c in result["missing_courses"]
                            if c.get("course_type") == "必修"]
        assert required_missing == [], f"必修不應有缺漏: {required_missing}"

    def test_group_a_passed_2(self):
        result = check_major(self.session, self.student, "資訊科學系")
        group_a_passed = [c for c in result["passed_courses"]
                          if c.get("group_label") == "群A"]
        assert len(group_a_passed) >= 2

    def test_group_violations_empty(self):
        result = check_major(self.session, self.student, "資訊科學系")
        assert result["group_violations"] == []

    def test_pe_complete(self):
        result = check_pe(self.session, self.student)
        assert result["status"] == "complete"
        assert result["passed_semesters"] == 4
        assert result["missing_semesters"] == 0

    def test_ge_complete(self):
        result = check_ge(self.session, self.student)
        assert result["status"] == "complete"

    def test_ge_core_domains_at_least_2(self):
        result = check_ge(self.session, self.student)
        assert len(result["core_domains"]) >= 2


# ─── StudentB：必修缺漏 ───────────────────────────────────────────────────────

class TestStudentB_MissingRequired:
    """演算法和作業系統沒修 → major incomplete，missing_courses 包含這兩門。"""

    @pytest.fixture(autouse=True)
    def setup(self, db_session):
        records = (
            _required_records(exclude_codes=(ALGO, OS))
            + [
                _rec(PROJ_A_021, "資訊專題（A）", req="群", score="88", credit="3.0"),
                _rec(PROJ_B,     "資訊專題（B）", req="群", score="90", credit="3.0"),
                _rec(AI_INTRO,   "人工智慧概論", req="群", score="88", credit="3.0"),
                _rec(COMP_GRAPH, "電腦圖學",     req="群", score="87", credit="3.0"),
                _rec(DIST_SYS,   "分散式系統",   req="群", score="82", credit="3.0"),
            ]
            + _ge_records()
            + _pe_records(4)
        )
        self.student = _import(db_session, "112703902", records)
        self.session = db_session

    def test_major_incomplete(self):
        result = check_major(self.session, self.student, "資訊科學系")
        assert result["status"] == "incomplete"

    def test_missing_algo(self):
        result = check_major(self.session, self.student, "資訊科學系")
        missing_codes = [c.get("course_code", "") for c in result["missing_courses"]]
        # 規則 code 是 703022001，可能直接存 703022001
        assert any("703022" in (c or "") for c in missing_codes), missing_codes

    def test_missing_os(self):
        result = check_major(self.session, self.student, "資訊科學系")
        missing_codes = [c.get("course_code", "") for c in result["missing_courses"]]
        assert any("703016" in (c or "") for c in missing_codes), missing_codes

    def test_req_only_missing_credits_correct(self):
        result = check_major(self.session, self.student, "資訊科學系")
        # 演算法3學分 + 作業系統3學分 = 6學分缺口
        assert result["req_only_missing"] == 6.0


# ─── StudentC：群修不足 ───────────────────────────────────────────────────────

class TestStudentC_InsufficientGroupCourses:
    """群A只1門、群B~E只覆蓋2個不同領域 → group_violations 不空。"""

    @pytest.fixture(autouse=True)
    def setup(self, db_session):
        records = (
            _required_records()
            + [
                # 群A 只修1門（不夠2門）
                _rec(PROJ_A_021, "資訊專題（A）", req="群", score="88", credit="3.0"),
                # 群B、C 各1門（只有2個領域，需要3個）
                _rec(AI_INTRO,   "人工智慧概論", req="群", score="88", credit="3.0"),
                _rec(COMP_GRAPH, "電腦圖學",     req="群", score="87", credit="3.0"),
                # 群D、E 都沒有
            ]
            + _ge_records()
            + _pe_records(4)
        )
        self.student = _import(db_session, "112703903", records)
        self.session = db_session

    def test_major_incomplete_due_to_group(self):
        result = check_major(self.session, self.student, "資訊科學系")
        assert result["status"] == "incomplete"

    def test_group_a_violation(self):
        result = check_major(self.session, self.student, "資訊科學系")
        viol_groups = [v["group"] for v in result["group_violations"]]
        assert "群A" in viol_groups

    def test_group_bce_shared_violation(self):
        """群B~E 共同規則（至少3個不同領域）也要觸發 violation。"""
        result = check_major(self.session, self.student, "資訊科學系")
        viol_groups = [v["group"] for v in result["group_violations"]]
        # _shared 的 group key 是 "群B+群C+群D+群E"
        assert any("群B" in g for g in viol_groups), viol_groups


# ─── StudentD：體育不足 ───────────────────────────────────────────────────────

class TestStudentD_InsufficientPE:
    """體育只2學期（需4）→ pe incomplete，missing_semesters=2。"""

    @pytest.fixture(autouse=True)
    def setup(self, db_session):
        records = (
            _required_records()
            + [
                _rec(PROJ_A_021, "資訊專題（A）", req="群", score="88", credit="3.0"),
                _rec(PROJ_B,     "資訊專題（B）", req="群", score="90", credit="3.0"),
                _rec(AI_INTRO,   "人工智慧概論", req="群", score="88", credit="3.0"),
                _rec(COMP_GRAPH, "電腦圖學",     req="群", score="87", credit="3.0"),
                _rec(DIST_SYS,   "分散式系統",   req="群", score="82", credit="3.0"),
            ]
            + _ge_records()
            + _pe_records(2)  # 只修2學期
        )
        self.student = _import(db_session, "112703904", records)
        self.session = db_session

    def test_pe_incomplete(self):
        result = check_pe(self.session, self.student)
        assert result["status"] == "incomplete"

    def test_pe_missing_semesters(self):
        result = check_pe(self.session, self.student)
        assert result["missing_semesters"] == 2

    def test_pe_passed_semesters(self):
        result = check_pe(self.session, self.student)
        assert result["passed_semesters"] == 2


# ─── StudentE：in_progress（正在修課） ─────────────────────────────────────────

class TestStudentE_InProgress:
    """演算法 score=成績未到或無成績 → in_progress_courses，不進 earned，不進 missing。"""

    @pytest.fixture(autouse=True)
    def setup(self, db_session):
        records = (
            _required_records(in_progress_codes=(ALGO,))
            + [
                _rec(PROJ_A_021, "資訊專題（A）", req="群", score="88", credit="3.0"),
                _rec(PROJ_B,     "資訊專題（B）", req="群", score="90", credit="3.0"),
                _rec(AI_INTRO,   "人工智慧概論", req="群", score="88", credit="3.0"),
                _rec(COMP_GRAPH, "電腦圖學",     req="群", score="87", credit="3.0"),
                _rec(DIST_SYS,   "分散式系統",   req="群", score="82", credit="3.0"),
            ]
            + _ge_records()
            + _pe_records(4)
        )
        self.student = _import(db_session, "112703905", records)
        self.session = db_session

    def test_algo_in_progress_not_earned(self):
        result = check_major(self.session, self.student, "資訊科學系")
        in_prog_codes = [c.get("course_code", "") for c in result["in_progress_courses"]]
        assert any("703022" in (c or "") for c in in_prog_codes), in_prog_codes

    def test_algo_not_in_missing(self):
        """in_progress 的課不應出現在 missing_courses。"""
        result = check_major(self.session, self.student, "資訊科學系")
        missing_codes = [c.get("course_code", "") for c in result["missing_courses"]]
        assert not any("703022" in (c or "") for c in missing_codes), missing_codes

    def test_in_progress_credits_nonzero(self):
        result = check_major(self.session, self.student, "資訊科學系")
        assert result["in_progress_credits"] > 0

    def test_status_incomplete_because_algo_not_yet_passed(self):
        result = check_major(self.session, self.student, "資訊科學系")
        # 演算法還沒過 → missing_credits > 0 → incomplete
        assert result["status"] == "incomplete"


# ─── StudentF：班次不同 prefix 比對 ───────────────────────────────────────────

class TestStudentF_CourseCodePrefix:
    """
    資訊專題（A）的學生課號是 703044021（班21）；
    規則是 703044001（班01）。
    前6碼 703044 相同 → 應該比得到。
    """

    @pytest.fixture(autouse=True)
    def setup(self, db_session):
        records = (
            _required_records()
            + [
                _rec("703044021", "資訊專題（A）", req="群", score="88", credit="3.0"),
                _rec("703044031", "資訊專題（B）", req="群", score="90", credit="3.0"),  # 班31
                _rec(AI_INTRO,   "人工智慧概論", req="群", score="88", credit="3.0"),
                _rec(COMP_GRAPH, "電腦圖學",     req="群", score="87", credit="3.0"),
                _rec(INFO_SEC,   "資訊安全",     req="群", score="85", credit="3.0"),
                _rec(DIST_SYS,   "分散式系統",   req="群", score="82", credit="3.0"),
            ]
            + _ge_records()
            + _pe_records(4)
        )
        self.student = _import(db_session, "112703906", records)
        self.session = db_session

    def test_group_a_matched_via_prefix(self):
        result = check_major(self.session, self.student, "資訊科學系")
        group_a_passed = [c for c in result["passed_courses"]
                          if c.get("group_label") == "群A"]
        assert len(group_a_passed) >= 2, (
            f"群A 應比到2門（透過前6碼），實際比到: {group_a_passed}"
        )

    def test_no_group_a_violation(self):
        result = check_major(self.session, self.student, "資訊科學系")
        viol_groups = [v["group"] for v in result["group_violations"]]
        assert "群A" not in viol_groups

    def test_matched_course_code_is_student_code(self):
        """比對結果的 course_code 應是學生實際的班次代碼，不是規則代碼。"""
        result = check_major(self.session, self.student, "資訊科學系")
        group_a_codes = [c["course_code"] for c in result["passed_courses"]
                         if c.get("group_label") == "群A"]
        # 學生的是 021 / 031 班，不是規則的 001
        assert any("703044021" == c or "703044031" == c for c in group_a_codes), group_a_codes


# ─── StudentG：通識各類別覆蓋 ─────────────────────────────────────────────────

class TestStudentG_GE:
    """測試通識 ge_label 分類、核心通識，以及資科系資訊通免修。"""

    @pytest.fixture(autouse=True)
    def setup(self, db_session):
        records = (
            _required_records()
            + [
                _rec(PROJ_A_021, "資訊專題（A）", req="群", score="88", credit="3.0"),
                _rec(PROJ_B,     "資訊專題（B）", req="群", score="90", credit="3.0"),
                _rec(AI_INTRO,   "人工智慧概論", req="群", score="88", credit="3.0"),
                _rec(COMP_GRAPH, "電腦圖學",     req="群", score="87", credit="3.0"),
                _rec(INFO_SEC,   "資訊安全",     req="群", score="85", credit="3.0"),
                _rec(DIST_SYS,   "分散式系統",   req="群", score="82", credit="3.0"),
            ]
            + _ge_records()
            + _pe_records(4)
        )
        self.student = _import(db_session, "112703907", records)
        self.session = db_session

    def test_chinese_ge_category_present(self):
        result = check_ge(self.session, self.student)
        cats = {c["remark_code"]: c for c in result["categories"]}
        assert cats["中文通"]["earned_credits"] >= 3.0

    def test_foreign_ge_category_present(self):
        result = check_ge(self.session, self.student)
        cats = {c["remark_code"]: c for c in result["categories"]}
        assert cats["外文通"]["earned_credits"] >= 6.0

    def test_info_ge_exempt_for_cs_major(self):
        """資科系學生資訊通 min=0，所以 status=complete 即使沒修。"""
        result = check_ge(self.session, self.student)
        cats = {c["remark_code"]: c for c in result["categories"]}
        assert cats["資訊通"]["credits_required_min"] == 0.0
        assert cats["資訊通"]["status"] == "complete"

    def test_core_domains_at_least_2(self):
        result = check_ge(self.session, self.student)
        assert len(result["core_domains"]) >= 2

    def test_ge_total_complete(self):
        result = check_ge(self.session, self.student)
        assert result["status"] == "complete"

