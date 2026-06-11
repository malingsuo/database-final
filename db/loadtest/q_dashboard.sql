-- Dashboard 最重的查詢：全表 enrollment × course JOIN + GROUP BY + 條件聚合
-- 對應系統 GET /api/admin/dashboard 的 _difficult_courses（課程失敗率排行）
-- 這是整個系統最吃 DB 的查詢：掃全部 enrollment(~17k) 做聚合
SELECT c.name,
       count(*) AS total,
       count(*) FILTER (
         WHERE e.is_passed = false
           AND e.grade IS NOT NULL
           AND e.grade <> ''
           AND e.grade <> '成績未到或無成績'
       ) AS failed
FROM enrollment e
JOIN course c
  ON c.course_code = e.course_code
 AND c.year = e.year
 AND c.semester = e.semester
GROUP BY c.name
HAVING count(*) FILTER (
         WHERE e.is_passed = false
           AND e.grade IS NOT NULL
           AND e.grade <> ''
           AND e.grade <> '成績未到或無成績'
       ) > 0
ORDER BY failed DESC
LIMIT 3;
