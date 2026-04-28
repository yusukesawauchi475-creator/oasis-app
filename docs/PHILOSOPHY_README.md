# Oasis Operations Philosophy

このディレクトリは Oasis の運用 philosophy を SSOT として管理する。

## ファイル構成
- core-philosophy.md: 原則1-6（不変）
- audit-checklist.md: push 前 audit 軸1-5
- post-mortems/: mistake 蓄積（mistake_date_short-name.md）

## 運用ルール
1. 各セッション開始時、CTO chat は core-philosophy.md と audit-checklist.md を読む
2. 修正実装前、audit-checklist.md の該当軸を mental simulation
3. mistake 発生時、post-mortems/ に追記（責任追求じゃなく学習）
4. CLAUDE.md と SSOT.md にも整合性 check

## 適用範囲
- Oasis のみ（Hum / Ippei は別 instance）
- philosophy framework は共通、project 固有 customize は許容
