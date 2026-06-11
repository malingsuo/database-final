// Baseline 壓測 — 建立「乾淨基準線」
//
// 目的：用最便宜、免驗證的端點 GET /api/public/departments（260 筆固定查詢），
//       階梯式加壓，量出 nginx 純轉發 + 單純 DB 查詢的吞吐與延遲基準。
//       之後 load/stress 的數字都對照這條基準解讀。
//
// 執行：
//   k6 run k6/baseline.js
//   k6 run -e BASE_URL=http://localhost:3030 k6/baseline.js

import http from 'k6/http';
import { check } from 'k6';
import { BASE } from './lib/common.js';

export const options = {
  scenarios: {
    baseline: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '30s', target: 20 },   // 暖機
        { duration: '1m', target: 50 },    // 穩定加壓
        { duration: '1m', target: 100 },   // 拉高
        { duration: '30s', target: 0 },    // 降載
      ],
      gracefulRampDown: '10s',
    },
  },
  thresholds: {
    // 免驗證的簡單查詢應該很快：p95 < 300ms、幾乎零錯誤
    http_req_duration: ['p(95)<300', 'p(99)<800'],
    http_req_failed: ['rate<0.005'],
    checks: ['rate>0.995'],
  },
};

export default function () {
  const res = http.get(`${BASE}/api/public/departments`, { tags: { name: 'departments' } });
  check(res, {
    'status 200': (r) => r.status === 200,
    'has departments': (r) => {
      try { return Array.isArray(r.json()) && r.json().length > 0; } catch (_) { return false; }
    },
  });
}
