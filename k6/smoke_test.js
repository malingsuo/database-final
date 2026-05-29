// K6 Smoke Test — 驗證 backend /health 端點是否正常回應
//
// 執行方式：
//   k6 run k6/smoke_test.js
//
// 前提：docker compose up 已啟動，nginx 監聽 http://localhost:3030

import http from 'k6/http';
import { check } from 'k6';

export const options = {
  vus: 1,
  duration: '10s',
};

export default function () {
  const res = http.get('http://localhost:3030/health');

  check(res, {
    'status is 200': (r) => r.status === 200,
  });
}
