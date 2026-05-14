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
~/oasis-app/                      ← Git root, Netlifyデプロイ元
├── index.html                    ← 本番SPA（2,250行）。Leaflet地図+全UIロジック
├── admin.html                    ← 管理画面（508行）。pending_toilets承認/却下UI
├── manifest.json                 ← PWA manifest（アイコン, テーマカラー）
├── oasis-logo.jpg                ← アプリロゴ（favicon, apple-touch-icon）
├── OASIS_SSOT.md                 ← 引き継ぎドキュメント（SSOT）
├── OASIS_QA.md                   ← 定期QAチェックリスト（11項目）
├── HYBRID_DESIGN.md              ← ハイブリッド設計ドキュメント
├── CLAUDE.md                     ← このファイル
├── netlify.toml                  ← Netlify設定（Cache-Control: no-cache）
├── firebase.json                 ← Firebase CLI設定（firestoreルール参照）
├── firestore.rules               ← Firestoreセキュリティルール
├── .gitignore                    ← node_modules, app/, supabase/, .csv除外
├── .github/workflows/
│   ├── nightly-qa.yml            ← 毎晩JST 02:00 Claude API経由でQA→自動issue作成
│   ├── nightly-cron.yml          ← 定期cronジョブ
│   └── monthly-refresh.yml      ← 月次データリフレッシュ
├── docs/
│   ├── core-philosophy.md        ← 設計思想
│   ├── audit-checklist.md        ← 監査チェックリスト
│   ├── handoff-template.md       ← 引き継ぎテンプレート
│   ├── PHILOSOPHY_README.md
│   └── post-mortems/
│       └── 2026-04-28_philosophy-violation.md
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

## 主要コンポーネント（index.html内、全2,250行）

| セクション | 行範囲(概算) | 内容 |
|---|---|---|
| CSS | 26-636 | 全スタイル（シート, マーカー, フィルター, 投票等） |
| HTML | 638-732 | DOM構造（#map, #bottom, #sheet, picker, nudge） |
| L10N | 733-813 | JP/EN翻訳辞書 |
| Firebase init | 851-861 | firebase.initializeApp, Firestore接続, 起動時ヘルスチェック |
| addUIOverlays | 878-919 | lang-toggle, adminモード（handleAdminTap） |
| TIER_CONFIG | 971-998 | brands[デッドコード], types[デッドコード], colors, display設定 |
| tierKey()/decideTierLocal() | 1005-1049 | Tier判定ロジック（JP/US/UK/AU分岐, majorTerminals） |
| makeIcon/clusterIcon | 1051-1068 | マーカーアイコン生成 |
| scoreToilets() | 1069-1079 | **デッドコード**（renderNearby()から呼ばれない） |
| refreshZoom() | 1105-1169 | マーカー描画（viewport/cluster切替, isRefreshingガード） |
| loadCity() | 1194-1270 | Firestore chunk並列fetch, キャッシュ(v6) |
| loadPendingToilets() | 1272-1294 | pending_toilets fetch（cityKeyフィルターなし） |
| renderCity() | 1310-1323 | allMarkers生成, applyFilter, renderNearby |
| renderNearby() | 1388-1452 | 近傍リスト（searchPin/GPS起点, stageExpand） |
| selectCity() | 1458-1483 | 都市ピッカーから選択 |
| openDetail() | 1562-1697 | 詳細シート（顔, 投票カウント, 3Dボタン） |
| answerQ1/Q2/Q3 | 1639-1697 | 3問レビューシステム（localStorage制限） |
| startInlineReview/submitReview | 1919-1975 | **デッドコード**（#28参照） |
| submitAdd/adminDirectAdd | 1810-1857 | トイレ追加（admin直接 or pending+EmailJS） |
| goToSearchResult() | 1996-2032 | 検索結果→地図移動+loadCity |
| switchTab() | 2034-2064 | タブ切替（Near Me / Search） |
| searchCity() | 2069-2121 | Google Places Text Search API |
| renderInlineLegend() | 2126-2142 | 凡例描画（T2_MINUS欠落 #40参照） |
| applyLang() | 2178-2195 | UI文字列更新（HUD/検索placeholder未更新 #33/#60参照） |
| init() | 2200-2247 | 起動フロー（geolocation, loadCity, 訪問者カウンター） |

## Firestore構造

```
oasis-bde20/
├── cities/{cityKey}/chunks/{0-14}  ← トイレデータ本体（~41,580件, 15都市）
├── reviews/                        ← 3問レビュー（access/refused/closed/cleanliness/paperSpace）
├── reviewSummaries/{toiletId}      ← 集計（access, refused, closed カウント）
├── reports/                        ← 問題報告（toiletId, reason）
├── pending_toilets/                ← ユーザー追加申請（status: pending/approved）
└── stats/visitors                  ← 訪問者カウンター（total, today, lastDate）
```

## 既知の主要バグ（Open Issues サマリ）

| Issue | Severity | 概要 |
|---|---|---|
| #36 | High/Security | firestore.rules: cities/chunks allow write: if true |
| #28 | High | startInlineReview()/submitReview() デッドコード（nudgeReview機能不全） |
| #27 | High | answerQ3() Firestore失敗時もlocalStorageに投票済みフラグが残る |
| #58 | Medium | init() geoHandled競合: GPS高速取得時にloadCity()がスキップされる |
| #55 | Medium | nightly-qa.yml モデルID obsolete（silent fail リスク） |
| #50 | Medium | openDetail() reviews全件fetch（.limit()なし） |
| #57 | Medium | pending/admin追加トイレ tier:1（数値）→ 常にT4で表示 |
| #35 | Medium | TIER_CONFIG.brands/typesがデッドコード（decideTierLocal未参照） |
| #31 | Medium | Whole Foods/Target/Trader Joe'sがT2_PLUSに誤分類 |
| #46 | Low/Doc | CLAUDE.md行番号乖離（本issueで修正済み） |
