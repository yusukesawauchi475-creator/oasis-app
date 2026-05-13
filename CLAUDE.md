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
  - Deploy回数制限なし（技術制約なし、Netlify無料枠内で実質無制限）
  - 全pushは diff 確認後のみ実行
  - ユーザー影響ある修正は最優先で即push OK（待たせない）
  - 同じバグで3回以上push繰り返したら立ち止まる（根本原因未解決の証拠）
  - 大規模リファクタや新機能追加はロールバック容易性のため小さく分割
  - deployは俺（オーナー）の明示指示後のみ
  - エラーが出ても即deployしない。原因特定してから1発で直す

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
├── index.html                    ← 本番SPA（~2,250行）。Leaflet地図+全UIロジック
├── admin.html                    ← 管理画面（パスワード保護、ダッシュボード/申請/レビュー）
├── manifest.json                 ← PWAマニフェスト
├── oasis-logo.jpg                ← アプリロゴ（favicon, apple-touch-icon）
├── OASIS_SSOT.md                 ← 引き継ぎドキュメント（SSOT）
├── OASIS_QA.md                   ← 夜間QAチェックリスト（11項目）
├── HYBRID_DESIGN.md              ← ハイブリッドデータアーキテクチャ設計
├── CLAUDE.md                     ← このファイル
├── netlify.toml                  ← Netlify設定（Cache-Control: no-cache）
├── firebase.json                 ← Firebase CLI設定（firestoreルール参照）
├── firestore.rules               ← Firestoreセキュリティルール
├── .gitignore                    ← node_modules, app/, supabase/, .csv除外
├── .github/workflows/            ← GitHub Actions
│   ├── nightly-qa.yml            ← 毎日JST 02:00、Claude APIでQA→issue自動作成
│   ├── nightly-cron.yml          ← 毎日JST 03:00、reports集計→Tier4自動降格
│   └── monthly-refresh.yml       ← 毎月1日JST 03:00、Places API新規place追加
├── scripts/                      ← audit/fix/ingestスクリプト（Python/Node）
│   ├── monthly_refresh.js        ← 月次データ更新（15都市）
│   ├── reports_aggregate.js      ← 報告集計・Tier4自動降格
│   ├── fix_all_cities.py         ← 全都市一括修正
│   ├── ingest_kobe.py / ingest_lodging.py ← ingestスクリプト
│   ├── fix_t4_promote.py / fix_tier3.py / fix_bbox_lodging.py ← 修正系
│   ├── audit_*.py / audit_*.mjs  ← 各種監査スクリプト
│   └── package.json              ← firebase-admin, node-fetch依存
├── docs/                         ← philosophy framework文書
│   ├── core-philosophy.md        ← 6原則
│   ├── audit-checklist.md        ← 5軸audit
│   ├── handoff-template.md       ← セッション引き継ぎテンプレート
│   ├── PHILOSOPHY_README.md
│   └── post-mortems/             ← ポストモーテム記録
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
| CSS | 27-590 | 全スタイル（シート, マーカー, フィルター, 投票等） |
| HTML | 595-730 | DOM構造（#map, #bottom, #sheet, picker, nudge） |
| L10N | 733-826 | JP/EN翻訳辞書（78キー）, setLang() |
| CITIES | 829-845 | 15都市定義（center/zoom/bbox）※kagoshima含む |
| Firebase init | 851-862 | firebase.initializeApp, Firestore接続, ヘルスチェック |
| addUIOverlays / initMap | 878-966 | lang-toggle, adminモード, マップ初期化 |
| TIER_CONFIG | 968-998 | brands, types, colors, display設定, TIER_WEIGHT |
| tierKey() / decideTierLocal() | 1003-1049 | Tier判定ロジック（JP/US/UK/AU分岐, majorTerminals） |
| makeIcon() / clusterIcon() | 1051-1068 | マーカーアイコン生成 |
| applyFilter() / refreshZoom() | 1081-1183 | フィルター適用, マーカー描画（isRefreshingガード, searchPin復元） |
| loadCity() | 1185-1270 | Firestore chunk並列fetch, キャッシュ(v6), progressiveロード |
| loadPendingToilets() | 1272-1308 | pending_toilets取得・地図表示（opacity:0.45） |
| renderCity() | 1310-1338 | allMarkers生成, applyFilter, renderNearby |
| renderNearby() / expandNearby() | 1376-1453 | 近傍リスト（searchPin/GPS起点, stageExpand） |
| selectCity() / updateHud() | 1458-1493 | 都市選択, HUD更新 |
| goToMe() / detectCity() | 1506-1543 | GPS取得, 都市自動検出 |
| openDetail() | 1562-1634 | 詳細シート（顔アイコン, 投票数, 3Dボタン） |
| answerQ1() / answerQ2() / answerQ3() | 1636-1697 | 3問タップ式レビュー（localStorage制限, reviewSummaries） |
| submitAdd() / adminDirectAdd() | 1810-1857 | トイレ追加（admin直接 or pending+EmailJS） |
| notifyNewToilet() / notifyNewReview() | 1864-1910 | EmailJS通知 |
| goToSearchResult() / switchTab() | 1980-2064 | 検索結果ナビ, タブ切替 |
| searchCity() | 2069-2121 | Google Places Text Search (New)（Autocompleteから移行済み） |
| renderInlineLegend() | 2126-2142 | 凡例（T1/T2P/T3/T4/PARTNER、タップ展開） |
| applyLang() | 2178-2195 | UI文字列更新 |
| init() | 2200-2247 | 起動フロー（geolocation, loadCity, 訪問者カウンター） |

## Firestore構造

```
oasis-bde20/
├── cities/{cityKey}/chunks/{0-14}  ← トイレデータ本体（15都市 × 最大15chunk）
├── reviews/                        ← 3問タップ式レビュー（access/cleanliness/paperSpace）
├── reviewSummaries/{toiletId}      ← 集計（access/refused/closed カウント）
├── reports/                        ← 問題報告（Tier4自動降格トリガー、3件以上で発動）
├── pending_toilets/                ← ユーザー追加申請（status: pending/approved）
└── stats/visitors                  ← 訪問者カウンター（total/today/lastDate）
```
