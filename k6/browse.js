// Browse 壓測 — 登入一次後持續瀏覽（最貼近真實使用者行為）
//
// 與 load.js 的差異：
//   load.js   = 每輪都重新登入（登入成本蓋過瀏覽，主要在量 argon2）
//   browse.js = 每個 VU 開場只登入一次，token 跨迭代重用，之後純瀏覽不重登
//
// 目的：隔離掉 argon2 登入成本，量「登入後的正常使用體驗」——
//       backend 處理畢業檢核/盤點的真實吞吐與延遲，以及 auth_request 驗 token 的開銷。
//
// 真實模型：學生登入一次 → session 期間反覆看檢核、刷新、看不同分頁。
//
// 執行：
//   k6 run k6/browse.js
//   k6 run -e STU_COUNT=500 k6/browse.js

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { BASE, randomStudent, login, authHeaders } from './lib/common.js';

export const options = {
  scenarios: {
    browse: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '1m', target: 50 },    // 暖機
        { duration: '2m', target: 100 },   // 100 個並發「已登入」使用者持續瀏覽
        { duration: '2m', target: 100 },   // 維持，看穩態
        { duration: '1m', target: 0 },
      ],
      gracefulRampDown: '15s',
    },
  },
  thresholds: {
    // 已登入後的瀏覽應該很順：p95 < 600ms（不含 argon2）
    http_req_duration: ['p(95)<600', 'p(99)<1500'],
    'http_req_duration{name:check}': ['p(95)<500'],
    'http_req_duration{name:login}': ['p(95)<1500'],  // 只在 VU 第一次跑時發生
    http_req_failed: ['rate<0.01'],
    checks: ['rate>0.99'],
  },
};

// VU 層級狀態：每個 VU 是獨立 JS runtime，這些變數跨迭代保留。
let vuStudent = null;   // 這個 VU 綁定的假學生
let vuToken = null;     // 這個 VU 的登入 token（登入一次後重用）

function ensureLoggedIn() {
  if (vuToken) return true;
  if (!vuStudent) vuStudent = randomStudent();
  group('login-once', () => {
    vuToken = login(vuStudent.email, vuStudent.password);
  });
  return vuToken !== null;
}

export default function () {
  // 第一次迭代才登入；之後直接重用 token
  if (!ensureLoggedIn()) {
    sleep(2);          // 登入失敗，稍候重試（下一輪會再 ensureLoggedIn）
    return;
  }

  // 模擬瀏覽行為：在不同動作間隨機切換，帶閱讀停頓
  const action = Math.random();

  if (action < 0.6) {
    // 60%：看自己的畢業檢核（最常見動作）
    const res = http.get(`${BASE}/api/check/${vuStudent.studentId}`, {
      ...authHeaders(vuToken),
      tags: { name: 'check' },
    });
    const ok = check(res, {
      'check 200': (r) => r.status === 200,
      'check has summary': (r) => {
        try { return r.json('summary') !== null; } catch (_) { return false; }
      },
    });
    // token 失效（如被清）→ 401，清掉重登
    if (res.status === 401) vuToken = null;
  } else if (action < 0.85) {
    // 25%：確認登入狀態 / 個人資料（auth /status，輕量）
    const res = http.get(`${BASE}/api/auth/status`, {
      ...authHeaders(vuToken),
      tags: { name: 'status' },
    });
    check(res, { 'status 200': (r) => r.status === 200 });
    if (res.status === 401) vuToken = null;
  } else {
    // 15%：看系所列表（公開資料，模擬切換分頁）
    const res = http.get(`${BASE}/api/public/departments`, {
      tags: { name: 'departments' },
    });
    check(res, { 'departments 200': (r) => r.status === 200 });
  }

  // 閱讀停頓 1~4 秒（真實使用者不會狂刷）
  sleep(Math.random() * 3 + 1);
}
