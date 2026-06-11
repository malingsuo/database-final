// Load 壓測 — 真實混合使用者場景
//
// 模擬真實學生流量：登入 → 看自己的畢業檢核（最重的 CPU 端點）→ 部分人再看一次。
// 每個 /api/check 都會觸發 nginx auth_request 驗 token，所以同時也壓 auth service。
//
// 目的：在預期尖峰負載下，量 p95/p99 latency 與錯誤率，找系統開始吃力的拐點。
//
// 執行：
//   k6 run k6/load.js
//   k6 run -e STU_COUNT=500 k6/load.js

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { BASE, randomStudent, login, authHeaders } from './lib/common.js';

export const options = {
  scenarios: {
    students: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '1m', target: 30 },    // 暖機到 30 並發學生
        { duration: '2m', target: 60 },    // 預期尖峰
        { duration: '2m', target: 60 },    // 維持尖峰（看穩態）
        { duration: '1m', target: 0 },     // 降載
      ],
      gracefulRampDown: '15s',
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<800', 'p(99)<2000'],
    'http_req_duration{name:login}': ['p(95)<1500'],   // argon2 較慢，放寬
    'http_req_duration{name:check}': ['p(95)<1000'],   // 畢業檢核 CPU 重
    http_req_failed: ['rate<0.01'],
    checks: ['rate>0.99'],
  },
};

export default function () {
  const stu = randomStudent();

  let token = null;
  group('login', () => {
    token = login(stu.email, stu.password);
  });
  if (!token) {
    sleep(1);
    return;
  }

  group('view-graduation-check', () => {
    const res = http.get(`${BASE}/api/check/${stu.studentId}`, {
      ...authHeaders(token),
      tags: { name: 'check' },
    });
    check(res, {
      'check 200': (r) => r.status === 200,
      'check has summary': (r) => {
        try { return r.json('summary') !== null; } catch (_) { return false; }
      },
    });
  });

  // 模擬使用者思考停頓
  sleep(Math.random() * 2 + 1);

  // 30% 的人會再刷新看一次
  if (Math.random() < 0.3) {
    http.get(`${BASE}/api/check/${stu.studentId}`, {
      ...authHeaders(token),
      tags: { name: 'check' },
    });
    sleep(1);
  }
}
