# Oasis App — CLAUDE.md

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
├── index.html                    ← 本番SPA（~2,100行）。Leaflet地図+全UIロジック
├── oasis-logo.jpg                ← アプリロゴ（favicon, apple-touch-icon）
├── OASIS_SSOT.md                 ← 引き継ぎドキュメント（SSOT）
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
| CSS | 17-590 | 全スタイル（シート, マーカー, フィルター, 投票等） |
| HTML | 595-720 | DOM構造（#map, #bottom, #sheet, picker, nudge） |
| L10N | 725-810 | JP/EN翻訳辞書 |
| Firebase init | 850-865 | firebase.initializeApp, Firestore接続 |
| addUIOverlays | 879-920 | lang-toggle, adminモード |
| TIER_CONFIG | 969-994 | brands, types, colors, display設定 |
| tierKey() | 1003-1025 | Tier判定ロジック（JP/US分岐, majorTerminals） |
| makeIcon/cluster | 1027-1040 | マーカーアイコン生成 |
| refreshZoom() | 1079-1145 | マーカー描画（viewport/cluster切替, isRefreshingガード） |
| loadCity() | 1160-1210 | Firestore chunk並列fetch, キャッシュ(v5) |
| renderCity() | 1215-1245 | allMarkers生成, applyFilter, renderNearby |
| renderNearby() | 1290-1330 | 近傍リスト（searchPin/GPS起点, stageExpand） |
| openDetail() | 1375-1455 | 詳細シート（星, 顔, 投票, 3Dボタン） |
| rateStar/quickVote | 1457-1495 | 星評価・投票（localStorage制限, reviewSummaries） |
| submitReview | 1610-1640 | 詳細レビュー送信 |
| submitAdd | 1640-1720 | トイレ追加（admin直接 or pending+EmailJS） |
| searchCity | 1895-1950 | Google Places Autocomplete (New) |
| goToPlaceId | 1952-1970 | Place Details → goToSearchResult |
| init() | 2035-2070 | 起動フロー（geolocation, loadCity, invalidateSize） |

## Firestore構造

```
oasis-bde20/
├── cities/{cityKey}/chunks/{0-14}  ← トイレデータ本体
├── reviews/                        ← 星評価・投票・詳細レビュー
├── reviewSummaries/{toiletId}      ← 集計（ratingTotal, access, refused等）
├── reports/                        ← 問題報告
└── pending_toilets/                ← ユーザー追加申請（status: pending/approved）
```
