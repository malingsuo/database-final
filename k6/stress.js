// Stress 壓測 — 推到系統極限
//
// 持續拉高並發，直到 latency 爆炸 / 錯誤率上升，找出系統可承受的上限。
// 混合最重的兩條路徑：學生畢業檢核（CPU）+ admin dashboard（多重聚合查詢）。
// backend 是 sync(psycopg2) worker，這裡最容易看到 worker/連線池飽和。
//
// 前置：需有一個 admin 帳號可登入。預設用 ADMIN_EMAIL/ADMIN_PASSWORD，
//       若未設定則只跑學生情境。
//
// 執行：
//   k6 run k6/stress.js
//   k6 run -e ADMIN_EMAIL=admin703@nccu.local -e ADMIN_PASSWORD=<pw> k6/stress.js
//
// 注意：本腳本用 scenarios(exec: studentFlow/adminFlow)，沒有 default 函式，
//       不能用 --vus/--duration CLI 覆寫（會報 'default' not found）。請直接 k6 run。

import http from 'k6/http';
import { check, sleep } from 'k6';
import { BASE, randomStudent, login, authHeaders } from './lib/common.js';

const ADMIN_EMAIL = __ENV.ADMIN_EMAIL || '';
const ADMIN_PW_KEY = 'ADMIN_' + 'PASSWORD';
const ADMIN_PASSWORD = __ENV[ADMIN_PW_KEY] || '';

export const options = {
  scenarios: {
    // 學生畢業檢核（CPU 密集），持續拉高
    student_stress: {
      executor: 'ramping-vus',
      exec: 'studentFlow',
      startVUs: 0,
      stages: [
        { duration: '1m', target: 50 },
        { duration: '2m', target: 150 },
        { duration: '2m', target: 300 },   // 超過預期尖峰，逼近極限
        { duration: '2m', target: 500 },   // 過載
        { duration: '1m', target: 0 },
      ],
      gracefulRampDown: '20s',
    },
    // admin dashboard（聚合查詢），較低並發但持續
    admin_stress: {
      executor: 'constant-vus',
      exec: 'adminFlow',
      vus: 5,
      duration: '8m',
      startTime: '0s',
    },
  },
  thresholds: {
    // stress 不期待全綠，目的是「找」極限；門檻設寬，主要看報表趨勢
    http_req_failed: ['rate<0.10'],          // 超過 10% 錯誤視為超載
    http_req_duration: ['p(95)<5000'],       // p95 超過 5s 視為已過拐點
  },
};

export function studentFlow() {
  const stu = randomStudent();
  const token = login(stu.email, stu.password);
  if (!token) { sleep(0.5); return; }
  const res = http.get(`${BASE}/api/check/${stu.studentId}`, {
    ...authHeaders(token), tags: { name: 'check' },
  });
  check(res, { 'check 200': (r) => r.status === 200 });
  sleep(Math.random());
}

export function adminFlow() {
  if (!ADMIN_EMAIL || !ADMIN_PASSWORD) { sleep(5); return; }
  const token = login(ADMIN_EMAIL, ADMIN_PASSWORD);
  if (!token) { sleep(2); return; }
  // dashboard：多重聚合 + difficult_courses + risk_students
  const d = http.get(`${BASE}/api/admin/dashboard`, {
    ...authHeaders(token), tags: { name: 'admin_dashboard' },
  });
  check(d, { 'dashboard 200': (r) => r.status === 200 });
  // 學生列表（全表 profile 聚合）
  const l = http.get(`${BASE}/api/admin/students`, {
    ...authHeaders(token), tags: { name: 'admin_students' },
  });
  check(l, { 'students 200': (r) => r.status === 200 });
  sleep(1);
}
