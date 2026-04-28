# Push前 Audit Checklist

## 軸1: 副作用チェック
- この修正が呼び出す/呼び出される関数を全部確認したか？
- グローバル状態変数への影響を全部列挙したか？

## 軸2: 対称性チェック
- 状態を変える処理の「戻し側」は対称になっているか？
- 例: goToSearchResult と switchTab('near') は対称か？

## 軸3: エントリポイント横断チェック
- 同じロジックが他のエントリポイントにも必要ではないか？
- 例: switchTab に入れた修正を goToSearchResult / selectCity / goToMe にも入れたか？

## 軸4: キャッシュ・競合チェック
- isLoadingCity / currentLoadKey のガードは正しく機能するか？
- 並行 fetch が走った場合の動作を確認したか？

## 軸5: 実機フロー確認
- 修正後に BOSS が試すべき具体的なフローを列挙したか？
- DevTools console で確認すべきログを明記したか？
