// k6 共用設定與工具函式
//
// 所有腳本透過 nginx(3030) 打 API，與真實使用者路徑一致。
// 假學生資料由 scripts/seed_load_test_data.py 灌入（學號 112703101~，密碼 loadtest123）。

import http from 'k6/http';
import { check } from 'k6';

// ── 基本設定（可用環境變數覆寫）─────────────────────────
export const BASE = __ENV.BASE_URL || 'http://localhost:3030';

// 假學生範圍：學號 112703<seq>，seq 從 START 起、共 COUNT 名。
// 與 seed_load_test_data.py 的 STUDENT_ID_START / --count 對應。
export const STU_START = parseInt(__ENV.STU_START || '101', 10);
export const STU_COUNT = parseInt(__ENV.STU_COUNT || '500', 10);
export const STU_PASSWORD = __ENV.STU_PASSWORD || 'loadtest123';

// ── 工具：隨機挑一名假學生 ────────────────────────────
export function randomStudent() {
  const seq = STU_START + Math.floor(Math.random() * STU_COUNT);
  const s = String(seq).padStart(3, '0');
  return {
    seq,
    studentId: `112703${s}`,
    email: `loadtest_stu${s}@test.local`,
    password: STU_PASSWORD,
  };
}

// ── 工具：登入，回傳 token（失敗回 null）──────────────────
export function login(email, password) {
  const res = http.post(
    `${BASE}/api/auth/login`,
    JSON.stringify({ email, password }),
    { headers: { 'Content-Type': 'application/json' }, tags: { name: 'login' } },
  );
  const ok = check(res, {
    'login 200': (r) => r.status === 200,
    'login has token': (r) => {
      try { return !!r.json('access_token'); } catch (_) { return false; }
    },
  });
  if (!ok) return null;
  try { return res.json('access_token'); } catch (_) { return null; }
}

export function authHeaders(token) {
  return { headers: { Authorization: `Bearer ${token}` } };
}

// ── 共用 thresholds（SLO）──────────────────────────────
// p95 < 800ms、p99 < 2s、HTTP 錯誤率 < 1%。各腳本可覆寫。
export const DEFAULT_THRESHOLDS = {
  http_req_duration: ['p(95)<800', 'p(99)<2000'],
  http_req_failed: ['rate<0.01'],
  checks: ['rate>0.99'],
};
