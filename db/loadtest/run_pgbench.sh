#!/usr/bin/env bash
# pgbench 資料庫壓測主控腳本
#
# 直接連 PostgreSQL（跳過 nginx/auth/backend），量 DB 本身的極限。
# 與 k6（測整條鏈）互補：這裡隔離出「資料庫層」的 TPS / latency / 連線上限。
#
# 用法：
#   ./db/loadtest/run_pgbench.sh <mode> <query>
#     mode  : baseline | load | stress | spike
#     query : simple | student | dashboard | token   （預設 student）
#
# 範例：
#   ./db/loadtest/run_pgbench.sh baseline student
#   ./db/loadtest/run_pgbench.sh load dashboard
#   ./db/loadtest/run_pgbench.sh stress student
#   ./db/loadtest/run_pgbench.sh spike token
#
# 前置：docker compose up -d db 已啟動，且已灌假資料
#       （scripts/seed_load_test_data.py --count 500）
set -euo pipefail

MODE="${1:-load}"
QUERY="${2:-student}"

# ── DB 連線（在 db container 內跑 pgbench，連 localhost）──────────
DB_USER="${DB_USER:-postgres}"
DB_NAME="${DB_NAME:-dbfinal}"
CONTAINER="${DB_CONTAINER:-database-final-db-1}"

# ── 對應 query 檔 ──────────────────────────────────────────────
case "$QUERY" in
  simple)    SQL=q_simple.sql ;;
  student)   SQL=q_student_check.sql ;;
  dashboard) SQL=q_dashboard.sql ;;
  token)     SQL=q_token.sql ;;
  *) echo "未知 query：$QUERY（可用 simple|student|dashboard|token）"; exit 1 ;;
esac

# db/ 目錄已掛進 container 的 /docker-entrypoint-initdb.d/（見 docker-compose.yml），
# 所以 loadtest 子目錄在 container 內路徑為：
SQL_IN_CONTAINER="/docker-entrypoint-initdb.d/loadtest/$SQL"

# ── 各 mode 的 pgbench 參數 ────────────────────────────────────
# -c 連線數(clients)  -j 執行緒(jobs)  -T 持續秒數  -P 每幾秒印一次進度
run() {
  local clients="$1" jobs="$2" dur="$3"
  echo "════════════════════════════════════════════════"
  echo "  pgbench  mode=$MODE  query=$QUERY  (-c $clients -j $jobs -T $dur)"
  echo "════════════════════════════════════════════════"
  docker exec -i "$CONTAINER" \
    pgbench -U "$DB_USER" -d "$DB_NAME" \
      -c "$clients" -j "$jobs" -T "$dur" -P 5 \
      -n -f "$SQL_IN_CONTAINER" \
      --no-vacuum
}

case "$MODE" in
  # 單連線基準：1 client，看單筆 latency 底線
  baseline)
    run 1 1 20
    ;;
  # 穩定並發：固定 20 連線持續跑，看穩態 TPS / latency
  load)
    run 20 4 60
    ;;
  # 連線數階梯爬升：找 TPS 不再上升、latency 爆炸的拐點
  # 階梯停在 max_connections(預設100) 以下；想看「連線被拒」用 spike 模式。
  # 單階失敗(|| true)不中斷整個迴圈。
  stress)
    for c in 10 30 50 80 95; do
      j=$(( c < 8 ? c : 8 ))
      run "$c" "$j" 30 || true
      echo ""
    done
    ;;
  # 瞬間連線暴衝：用 -C 每筆交易都重建連線，模擬「連線建立/拆除風暴」
  # （PG 每連線 fork 一個 process，建連線本身就是成本）。
  # 連線數設 90（max_connections=100 扣掉保留），避免直接撞牆 abort 拿不到報表。
  # 想看「連線被拒」的極限，把 90 改成 200 即可重現 FATAL: too many clients。
  spike)
    docker exec -i "$CONTAINER" \
      pgbench -U "$DB_USER" -d "$DB_NAME" \
        -c 90 -j 8 -T 30 -P 5 \
        -C -n -f "$SQL_IN_CONTAINER" \
        --no-vacuum
    ;;
  *)
    echo "未知 mode：$MODE（可用 baseline|load|stress|spike）"; exit 1 ;;
esac
