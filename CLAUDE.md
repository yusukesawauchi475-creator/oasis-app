# Oasis App — CLAUDE.md

## Claude Code起動コマンド
セッション開始時は必ず以下で起動：
```
claude --dangerously-skip-permissions
```
これで全確認ダイアログをスキップ。

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

## 自律的QA実行ルール
セッション終盤や「次何する」と聞かれた時、指示を待たずに以下を自動実行：

1. OASIS_QA.md の10項目全チェック
2. 実機動作想定シミュレーション：
   - 全ボタンのonclick接続確認
   - 前進/戻る動作の整合性
   - JP/ENモードでの全画面チェック
   - ローディング・エラーハンドリング
3. 問題があればseverity付きでリストアップ
4. 修正案を提示（実行はオーナー承認後）

QAは「言われなくてもやる」ことが前提。

## ファイル構成

```
~/Oasis/                          ← Git root, Netlifyデプロイ元
├── index.html                    ← 本番SPA（~2,175行）。Leaflet地図+全UIロジック
├── admin.html                    ← 管理者ダッシュボード（~445行）。pending承認・レビュー管理
├── manifest.json                 ← PWA manifest（アイコン, テーマカラー等）
├── oasis-logo.jpg                ← アプリロゴ（favicon, apple-touch-icon）
├── OASIS_SSOT.md                 ← 引き継ぎドキュメント（SSOT）
├── OASIS_QA.md                   ← 定期QAプロンプト（10項目チェックリスト）
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
| CSS | 26-637 | 全スタイル（シート, マーカー, フィルター, 投票等） |
| HTML | 639-735 | DOM構造（#map, #bottom, #sheet, picker, nudge） |
| L10N | 739-815 | JP/EN翻訳辞書 |
| Firebase init | 847-870 | firebase.initializeApp, Firestore接続 |
| addUIOverlays | 874-915 | lang-toggle, adminモード（5回タップ解除） |
| initMap() | 916-962 | Leaflet地図初期化, タイル, click/zoom イベント |
| TIER_CONFIG | 967-994 | brands, types, colors, display設定 |
| tierKey() | 1001-1032 | Tier判定ロジック（JP/US分岐, majorTerminals） |
| makeIcon/cluster | 1033-1085 | マーカーアイコン生成 |
| refreshZoom() | 1086-1172 | マーカー描画（viewport/cluster切替, isRefreshingガード） |
| loadCity() | 1174-1248 | Firestore chunk並列fetch, キャッシュ(v6) |
| renderCity() | 1288-1365 | allMarkers生成, applyFilter, renderNearby |
| renderNearby() | 1366-1416 | 近傍リスト（searchPin/GPS起点, stageExpand） |
| openDetail() | 1521-1602 | 詳細シート（星, 顔, 投票, 3Dボタン, reviews fetch） |
| rateStar/quickVote | 1604-1750 | 星評価・投票（localStorage制限, reviewSummaries） |
| submitAdd | 1753-1800 | トイレ追加（admin直接 or pending+EmailJS） |
| submitReview | 1894-1918 | 詳細レビュー送信（inline review フロー） |
| goToSearchResult | 1939-1967 | 検索結果→地図移動・searchPin配置・loadCity |
| searchCity | 1986-2046 | Google Places Text Search API呼び出し・結果表示 |
| init() | 2125-2172 | 起動フロー（geolocation, loadCity, invalidateSize） |

## Firestore構造

```
oasis-bde20/
├── cities/{cityKey}/chunks/{0-14}  ← トイレデータ本体
├── reviews/                        ← 星評価・投票・詳細レビュー
├── reviewSummaries/{toiletId}      ← 集計（ratingTotal, access, refused等）
├── reports/                        ← 問題報告
└── pending_toilets/                ← ユーザー追加申請（status: pending/approved）
```
