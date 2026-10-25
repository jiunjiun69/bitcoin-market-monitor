# Bitcoin Market Monitor

一個不用 GCP、LINE 或資料庫的 BTC 投資研究儀表板，使用 **GitHub Actions + GitHub Pages**。網站只收集公開行情，沒有個人部位、成本或 API 金鑰。

## 功能

- BTC 價格及 50／200／300 週均線
- 新增 MSTR 最新股價卡片與獨立歷史線圖；BTC / MSTR 同期比較區共用 30D、90D、1Y、ALL 的實際日期範圍、各自美元刻度，並計算在共同交易日期起訖的同期漲跌幅。MSTR 休市日不補值，BTC 與美股日收盤時區不同，對比屬於研究參考。
- MSTR/BTC 相對強弱（美股收盤相對前一根已完成的 BTC UTC 日線，屬時間錯位近似）
- mnav.com 第三方 Strategy mNAV（非 Strategy 官方淨資產計算口徑）
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
| mNAV | https://www.mnav.com/mnav/strategy 第三方公開網頁數值及其網站更新日期，非官方淨資產口徑 | 5 日 |
| MVRV Z | https://github.com/akpasz/btc-data kpis.json；Coin Metrics 公開資料重建，不是 Glassnode | 3 日 |

來源錯誤或逾期顯示「資料暫缺」，不把舊數據當成最新。mNAV 只要取得有效當期數值，即顯示目前的溢／折價及是否高於研究參考線 1.50x；高位收縮趨勢必須另外累積至少 16 筆同口徑的近期歷史值。趨勢建立中只放次要說明，不等於資料異常，也不代表完整的牛市風險已解除。第三方 mNAV 的更新日期可能與美股實際報價日不同；不能將不同公式串接比較。

**研究規則（未經回測校準）**：
- mNAV：40 日峰值 ≥1.5x 且收縮 ≥15%，需至少 16 筆
- MSTR/BTC：20 個交易日相對變化 ≤−8%，且跌破其 20 日平均
- MVRV：Z-Score ≥3.5
- 週線：完整週 K 收盤價跌破 50W SMA

研究分級是觀察輔助，不代表投資建議或價格預測。不可將私人交易資料、資產、API 金鑰放入公開網站。

GitHub 儲存庫：https://github.com/jiunjiun69/bitcoin-market-monitor
