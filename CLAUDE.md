# Oasis App — CLAUDE.md

## ⚠️ DEPLOY RULES - 絶対厳守

**deployは俺（オーナー）が「deploy」と明示的に言った時のみ。**

以下は全部禁止：
- 「全部OKならgit push」のような条件付き指示でのauto push
- 確認後に自動でpush
- 「push する」と自己判断してpush

deployまでの必須フロー：
1. コード修正
2. auditして問題なし確認
3. 「確認頼む」でオーナーに報告
4. オーナーが「deploy」または「git push」と明示的に言う
5. 初めてpush実行

違反した場合：そのセッションでのdeploy権限を剥奪。

## Key rules

- **Places APIインジェスト承認制：** 新都市追加・再インジェスト前に必ずコスト試算をオーナーに提示し、明示的なYesをもらうまで実行禁止。$200月次クレジットは2025年3月廃止済み。全額実費。

- **デプロイルール（厳守）：**
  - 1セッション最大5 deploys
  - デプロイ前にコード確認必須
  - 同じエラーで3回失敗したらアプローチ変更、デプロイ停止
  - エラーが出ても即デプロイしない。原因特定してから1発で直す

## ファイル構成

```
~/Oasis/                          ← Git root, Netlifyデプロイ元
├── index.html                    ← 本番SPA（~2,128行）。Leaflet地図+全UIロジック
├── admin.html                    ← 管理者ダッシュボード（pending承認, レビュー管理, 統計）
├── oasis-logo.jpg                ← アプリロゴ（favicon, apple-touch-icon）
├── OASIS_SSOT.md                 ← 引き継ぎドキュメント（SSOT）
├── OASIS_QA.md                   ← 毎晩実行するルーティンQAチェックプロンプト
├── CLAUDE.md                     ← このファイル
├── netlify.toml                  ← Netlify設定（Cache-Control: no-cache）
├── firebase.json                 ← Firebase CLI設定（firestoreルール参照）
├── firestore.rules               ← Firestoreセキュリティルール
├── .gitignore                    ← node_modules, app/, supabase/, .csv除外
├── scripts/                      ← 過去のaudit/fix/ingestスクリプト（Python/Node）
│   ├── fix_all_cities.py
│   ├── ingest_kobe.py
│   └── ...
├── app/                          ← React Native (Expo) 旧版。.gitignore除外。未使用
└── supabase/                     ← Supabase functions。.gitignore除外。未使用

~/oasis-ingest/                   ← Firestore管理スクリプト（別ディレクトリ、Git管理外）
├── serviceAccountKey.json        ← Firebase Admin SDK鍵
├── ingest.js                     ← Google Places APIインジェスト
├── ingest_partners.js            ← IBDパートナーインジェスト（未実行）
├── approve_citypoint.js          ← pending_toilets承認スクリプト
├── analyze_kobe.js               ← 都市データ分析
├── investigate.js                ← Manhattanデータ調査
├── check_reviews.js              ← reviewsコレクション確認
├── list_pending.js               ← pending_toilets一覧
├── count_partners.js             ← isPartner件数確認
├── count_west_manhattan.js       ← Weehawken側データ件数
└── package.json                  ← firebase-admin依存

~/Downloads/OASIS_SSOT.md         ← SSOTのバックアップ（Downloads内）
```

## 主要コンポーネント（index.html内）

| セクション | 行範囲(概算) | 内容 |
|---|---|---|
| CSS | 17-628 | 全スタイル（シート, マーカー, フィルター, 投票等） |
| HTML | 630-728 | DOM構造（#map, #bottom, #sheet, picker, nudge） |
| L10N | 730-820 | JP/EN翻訳辞書 |
| Firebase init | 854-880 | firebase.initializeApp, Firestore接続 |
| addUIOverlays | 881-922 | lang-toggle, adminモード |
| initMap() | 923-973 | Leaflet初期化, zoom/moveendイベント |
| TIER_CONFIG | 974-1007 | brands, types, colors, display設定 |
| tierKey() | 1008-1033 | Tier判定ロジック（JP/US分岐, majorTerminals） |
| makeIcon/cluster | 1034-1063 | マーカーアイコン生成 |
| applyFilter() | 1079-1086 | フィルター適用（searchPin復元含む） |
| refreshZoom() | 1087-1152 | マーカー描画（viewport/cluster切替, isRefreshingガード） |
| loadCity() | 1175-1250 | Firestore chunk並列fetch, キャッシュ(v5) |
| loadPendingToilets() | 1251-1288 | pending_toilets取得・マーカー表示 |
| renderCity() | 1289-1304 | allMarkers生成, applyFilter, renderNearby |
| renderNearby() | 1358-1425 | 近傍リスト（searchPin/GPS起点, stageExpand） |
| selectCity() | 1426-1449 | 都市切り替え（HUD更新, loadCity） |
| openDetail() | 1513-1595 | 詳細シート（星, 顔, 投票, 3Dボタン） |
| rateStar/quickVote | 1596-1631 | 星評価・投票（localStorage制限, reviewSummaries） |
| submitAdd | 1738-1821 | トイレ追加（admin直接 or pending+EmailJS）, notifyNewToilet |
| startInlineReview | 1822-1882 | インラインレビューフロー |
| submitReview | 1854-1882 | 詳細レビュー送信 |
| goToSearchResult | 1897-1923 | 検索結果 → loadCity → map.setView |
| searchCity | 1940-2003 | Google Places Autocomplete (New) |
| renderInlineLegend | 2004-2024 | Tier凡例レンダリング |
| openPicker() | 2025-2044 | 都市選択ピッカー |
| init() | 2078-2127 | 起動フロー（geolocation, loadCity, invalidateSize） |

## Firestore構造

```
oasis-bde20/
├── cities/{cityKey}/chunks/{0-14}  ← トイレデータ本体
├── reviews/                        ← 星評価・投票・詳細レビュー
├── reviewSummaries/{toiletId}      ← 集計（ratingTotal, access, refused等）
├── reports/                        ← 問題報告
└── pending_toilets/                ← ユーザー追加申請（status: pending/approved）
```
