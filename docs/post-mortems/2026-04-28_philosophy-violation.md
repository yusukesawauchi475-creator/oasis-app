# Philosophy 違反 post-mortem (2026-04-28)

## 何が起きたか
philosophy framework を docs/ に追加した直後、同じセッション内で BOSS から「md 毎回更新してるのか？」と指摘されるまで SSOT 更新を1回も実行しなかった。

## 違反した原則
- core-philosophy 原則6（BOSS visibility 依存禁止）
- audit-checklist 軸5（SSOT 更新）

## 根本原因
philosophy 導入と並行で複数トラック進行（cluster修正→philosophy作成→audit→新schema設計）。SSOT 更新を「あとでまとめて」と先延ばしし、BOSS 指摘まで気付かなかった。

## 再発防止
- 各 commit に SSOT 更新を含める運用にする
- 各 phase 完了時に「SSOT 該当箇所を sed で表示して照合」を audit-checklist に明記
- philosophy framework 導入セッション直後は特に意識する
