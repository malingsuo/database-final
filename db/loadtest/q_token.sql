-- Token 表讀寫：模擬 auth 驗證(SELECT) + 登入發 token(INSERT)
-- 對應每個受保護 API 的 nginx auth_request 查 token，以及 login 寫 token。
-- 注意：這是「DB 層」的 token 操作成本，不含 argon2（argon2 在應用層，DB 不參與）。
--
-- 先模擬一次驗證查詢（auth_request 每次都做）
\set acc random(1, 500)
SELECT t.account_id, a.role
FROM token t
JOIN account a ON a.id = t.account_id
LIMIT 1;
-- 再模擬一次登入發 token（INSERT）。用固定假 account 避免 FK 失敗。
-- 取一個存在的 account_id 寫入新 token。
INSERT INTO token (account_id, token)
SELECT id, md5(random()::text || clock_timestamp()::text)
FROM account
WHERE role = 'student'
LIMIT 1;
