-- 畢業檢核的核心讀取：enrollment × course 複合 key JOIN，取單一學生全部修課
-- 對應系統 check_graduation 從 DB 撈學生修課的部分（不含 Python 端比對計算）
-- 隨機挑一名假學生（學號 112703101 ~ 112703600）
\set seq random(101, 600)
SELECT e.course_code, e.year, e.semester, e.grade, e.is_passed,
       e.required_or_elective, e.remark,
       c.name, c.credits, c.type, c.ge_label
FROM enrollment e
JOIN course c
  ON c.course_code = e.course_code
 AND c.year = e.year
 AND c.semester = e.semester
WHERE e.student_id = '112703' || lpad(:seq::text, 3, '0');
