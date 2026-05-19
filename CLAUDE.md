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
├── index.html                    ← 本番SPA（2,250行）。Leaflet地図+全UIロジック
├── admin.html                    ← 管理画面（508行）。Firestore直接操作
├── oasis-logo.jpg                ← アプリロゴ（favicon, apple-touch-icon）
├── manifest.json                 ← PWA manifest（アイコン, theme-color等）
├── OASIS_SSOT.md                 ← 引き継ぎドキュメント（SSOT）
├── HYBRID_DESIGN.md              ← ハイブリッドデータアーキテクチャ設計メモ
├── CLAUDE.md                     ← このファイル
├── OASIS_QA.md                   ← 毎晩QAプロンプト（11項目）
├── netlify.toml                  ← Netlify設定（Cache-Control: no-cache）
├── firebase.json                 ← Firebase CLI設定（firestoreルール参照）
├── firestore.rules               ← Firestoreセキュリティルール
├── .gitignore                    ← node_modules, app/, supabase/, .csv除外
├── .github/workflows/
│   ├── nightly-qa.yml            ← 毎晩JST 02:00 Claude APIでQA実行（head -2200バグあり: #62）
│   ├── nightly-cron.yml          ← 毎晩JST 03:00 reports集計（scripts/reports_aggregate.js）
│   └── monthly-refresh.yml      ← 毎月1日JST 03:00 Places APIリフレッシュ（コスト承認必須: #22）
├── docs/
│   ├── PHILOSOPHY_README.md
│   ├── audit-checklist.md
│   ├── core-philosophy.md
│   ├── handoff-template.md
│   └── post-mortems/
├── scripts/                      ← audit/fix/ingest/aggregateスクリプト（Python/Node）
│   ├── monthly_refresh.js        ← Places API月次更新（totalNewバグ: #21）
│   ├── reports_aggregate.js      ← reports集計（nightly-cron.ymlから呼ばれる）
│   ├── fix_all_cities.py
│   ├── fix_bbox_lodging.py
│   ├── fix_manhattan.py
│   ├── fix_t4_promote.py
│   ├── fix_tier3.py
│   ├── ingest_kobe.py
│   ├── ingest_lodging.py
│   ├── audit_*.py / audit_*.mjs  ← 各種auditスクリプト
│   └── package.json              ← firebase-admin, node-fetch依存
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

## 主要コンポーネント（index.html内、2,250行）

| セクション | 行範囲(実測) | 内容 |
|---|---|---|
| CSS | 17-590 | 全スタイル（シート, マーカー, フィルター, 投票等） |
| HTML | 595-731 | DOM構造（#map, #bottom, #sheet, picker, nudge） |
| L10N | 738-813 | JP/EN翻訳辞書 |
| CITIES | 829-845 | 15都市定義（manhattan〜kagoshima）|
| Firebase init | 851-861 | firebase.initializeApp, Firestore接続 |
| addUIOverlays | 878-919 | lang-toggle, adminモード（handleAdminTap） |
| TIER_CONFIG | 971-996 | brands, types, colors, display設定（brandsはデッドコード: #35） |
| tierKey() / decideTierLocal() | 1005-1049 | Tier判定ロジック（JP/US/AU分岐, majorTerminals） |
| makeIcon / clusterIcon | 1051-1067 | マーカーアイコン生成 |
| scoreToilets() | 1069-1079 | デッドコード（renderNearby()から未呼出: #47） |
| TIER_EMOJI | 1363 | デッドコード定数（全コードで未参照） |
| refreshZoom() | 1104-1169 | マーカー描画（zoom≥14で個別バブル, 未満でクラスター） |
| loadCity() | 1194-1270 | Firestore chunk並列fetch, キャッシュ(v6), chunk0先行表示 |
| loadPendingToilets() | 1272-1294 | pending_toilets fetch（cityKeyフィルターなし: #43） |
| renderCity() | 1310-1323 | allMarkers生成, applyFilter, renderNearby |
| renderNearby() | 1388-1410 | 近傍リスト（searchPin/GPS起点, stageExpand, 5件初期表示） |
| expandNearby() | 1441-1453 | 「もっと見る」最大20件展開 |
| selectCity() | 1458-1483 | 都市選択（showLoading, searchPin設置, loadCity） |
| updateHud() | 1485-1493 | HUD都市名・フラグ更新 |
| setFilter() / applyFilter() | 1096-1102, 1498-1501 | フィルター切替 |
| detectCity() | 1537-1543 | GPS座標→cityKey判定（bbox照合） |
| openDetail() | 1562-1634 | 詳細シート（tier, 投票統計, 3-Questionレビュー, nav） |
| answerQ1/Q2/Q3() | 1639-1697 | 3段階レビュー（localStorage制限, Firestore書込） |
| listTapDetail() | 1718-1726 | リストtap→マーカーblink→openDetail |
| navWithNudge() / nav() | 1732-1743 | ルート案内（Google Maps） |
| openReport() / submitReport() | 1765-1783 | 問題報告→reports コレクション |
| openAddToilet() / submitAdd() | 1789-1829 | トイレ追加（admin直接 or pending+EmailJS） |
| adminDirectAdd() | 1831-1857 | admin直接追加（chunk 15回逐次fetch: #51） |
| notifyNewToilet/Review() | 1864-1910 | EmailJS通知（空catchバグ: #18） |
| startInlineReview() / submitReview() | 1919-1975 | デッドコードパス（nudge経由のみ: #28） |
| searchCity() | 2069-2121 | Google Places Text Search API（XSSリスク: #64） |
| goToSearchResult() | 1996-2032 | 検索結果→地図移動（showLoading()なし: #32） |
| switchTab() | 2034-2064 | タブ切替（loadCity前にshowLoading()なし: #54） |
| renderInlineLegend() | 2126-2142 | 凡例描画（T2_MINUSオレンジ省略: #40） |
| init() | 2200-2247 | 起動フロー（geoHandled常にfalse: #58, 訪問者カウンター） |

## Firestore構造

```
oasis-bde20/
├── cities/{cityKey}/chunks/{0-14}  ← トイレデータ本体
├── reviews/                        ← 星評価・投票・詳細レビュー
├── reviewSummaries/{toiletId}      ← 集計（ratingTotal, access, refused等）
├── reports/                        ← 問題報告
└── pending_toilets/                ← ユーザー追加申請（status: pending/approved）
```
