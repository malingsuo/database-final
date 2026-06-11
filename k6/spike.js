// Spike 壓測 — 瞬間流量尖峰
//
// 模擬「開放查詢的那一刻全班同時湧入登入」：並發數在數秒內暴衝。
// 主壓 POST /api/auth/login —— argon2 雜湊故意 CPU+記憶體密集（m=64MB,t=3,p=4），
// 是最容易被瞬間流量打垮的點。觀察 auth service 能否撐住、是否雪崩、回復多快。
//
// 執行：
//   k6 run k6/spike.js

import { check, sleep } from 'k6';
import { randomStudent, login } from './lib/common.js';

export const options = {
  scenarios: {
    spike: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '20s', target: 10 },    // 平常流量
        { duration: '10s', target: 300 },   // ⚡ 突然暴衝（尖峰）
        { duration: '1m', target: 300 },    // 維持尖峰
        { duration: '10s', target: 10 },    // 驟降
        { duration: '30s', target: 10 },    // 觀察回復
        { duration: '10s', target: 0 },
      ],
      gracefulRampDown: '10s',
    },
  },
  thresholds: {
    // spike 重點是「會不會雪崩 + 回復」，門檻寬鬆，主要看時間序列圖
    'http_req_duration{name:login}': ['p(95)<3000'],
    http_req_failed: ['rate<0.15'],
  },
};

export default function () {
  const stu = randomStudent();
  const token = login(stu.email, stu.password);
  check(null, { 'got token': () => token !== null });
  sleep(1);
}
