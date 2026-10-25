# Bitcoin Market Monitor

一個不用 GCP、LINE 或資料庫的 BTC 投資研究儀表板，使用 **GitHub Actions + GitHub Pages**。網站只收集公開行情，沒有個人部位、成本或 API 金鑰。

## 功能

- BTC 價格及 50／200／300 週均線
- MSTR/BTC 相對強弱（美股收盤相對前一根已完成的 BTC UTC 日線，屬時間錯位近似）
- Strategy 官方 mNAV（2026/07/23 後新定義，不與舊公式混用）
- MVRV Z-Score（公開重建資料，非 Glassnode 原始付費數據）
- 每個指標獨立顯示來源、日期、資料過期狀態
- 歷史圖表、四項研究風險訊號；不是自動交易策略

## 部署

1. 在 **Settings → Pages → Build and deployment → Source** 選擇 **GitHub Actions**。
2. 在 **Actions → Refresh data and deploy Pages → Run workflow** 手動執行第一次更新。
3. 成功後網站為 <https://jiunjiun69.github.io/bitcoin-market-monitor/>。
4. 每天 08:35 台灣時間排程更新；GitHub 定時執行可能延遲。
5. 如 Actions 無法提交 JSON，請在 Settings → Actions → General → Workflow permissions 開啟 Read and write permissions（若可設定）。

## 本機測試

    pip install -r requirements.txt pytest
    python -m pytest -q
    python scripts/market.py
    python scripts/build.py
    python -m http.server 8000 --directory dist

瀏覽 <http://localhost:8000>。

## 來源與限制

| 指標 | 資料來源 | 新鮮度 |
| --- | --- | --- |
| BTC | Coinbase Exchange BTC/USD daily candles | 2 日 |
| MSTR | Yahoo Finance 非官方 chart API（可能限流） | 5 日 |
| mNAV | https://www.strategy.com/ 官方頁面；需解析數值與標註的證券報價日期 | 5 日 |
| MVRV Z | https://github.com/akpasz/btc-data kpis.json；Coin Metrics 公開資料重建，不是 Glassnode | 3 日 |

來源錯誤或逾期一律顯示待驗證，絕不拿過期指標冒充即時訊號。mNAV 首次建站需要累積至少 16 筆同口徑資料，才會啟用高位收縮規則。

**研究規則（未經回測校準）**：
- mNAV：40 日峰值 ≥1.5x 且收縮 ≥15%，需至少 16 筆
- MSTR/BTC：20 個交易日相對變化 ≤−8%，且跌破其 20 日平均
- MVRV：Z-Score ≥3.5
- 週線：完整週 K 收盤價跌破 50W SMA

研究分級是觀察輔助，不代表投資建議或價格預測。不可將私人交易資料、資產、API 金鑰放入公開網站。

GitHub 儲存庫：https://github.com/jiunjiun69/bitcoin-market-monitor
