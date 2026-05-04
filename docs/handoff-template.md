# Oasis Handoff Template

新セッション開始時に BOSS が CTO chat に貼るテンプレ。

## 標準フォーマット
SSOT読んで。Oasis appのCTO頼む。
直近の状況: [前セッションで何をしたか1行]
今日やること: [タスク]

## 引き継ぎ確認事項
- [ ] OASIS_SSOT.md の残課題セクション確認
- [ ] docs/core-philosophy.md の原則確認
- [ ] git log --oneline -5 で直近コミット確認
- [ ] 未解決バグがあれば最優先で対応

## 注意事項
- deploy前に必ずdiff確認
- 同じバグ3回pushしたらアプローチ変更
- 「完了」宣言は実機確認後のみ
- 状態変数を変える修正は対称性確認必須

---

## セッション開始時の必須 fact 確認 protocol（2026-05-04 追加）

### 背景
Boss chat / CTO chat / Marketing chat の Claude.ai memory は derivative であり、
project 外（COO chat / Hermes / Telegram）の作業は自動同期されない。
真の Source of Truth は git repo + OASIS_SSOT.md のみ。

### 必須コマンド（新セッション最初に Claude Code に貼る）

```
セッション開始 fact 確認。

# SSOT version + 最終更新確認
head -30 ~/Oasis/OASIS_SSOT.md

# 直近 commit 把握（最低7日分）
cd ~/Oasis
git log --since="7 days ago" --pretty=format:"%h %ad %s" --date=short

# 未コミット変更確認
git status
git diff

# lib/ 状態確認（refactor 進捗）
ls -lat ~/oasis-ingest/lib/
grep -l "require.*lib/" ~/oasis-ingest/*.js | wc -l

結果を全文報告。memory ベース推測禁止、fact のみ。
```

この confirm が完了するまで、新規 task や修正の判断を開始しない。
philosophy 原則6（Visibility 依存禁止）+ Hum mistake 11（推測実装禁止）の物理 enforcement。

### 違反検出時の対応
Boss chat の memory が SSOT/git と乖離している場合:
- 即座に memory ベースの判断を停止
- 上記 fact 確認 protocol を再実行
- 乖離内容を post-mortems/ に記録（cross-chat sync failure）
