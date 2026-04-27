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
├── index.html                    ← 本番SPA（~2,230行）。Leaflet地図+全UIロジック
├── admin.html                    ← 管理ダッシュボード（~870行）。pending承認/downgrade確認/レビュー管理
├── oasis-logo.jpg                ← アプリロゴ（favicon, apple-touch-icon）
├── manifest.json                 ← PWAマニフェスト
├── OASIS_SSOT.md                 ← 引き継ぎドキュメント（SSOT）
├── OASIS_QA.md                   ← 毎晩QAプロンプト（11項目チェックリスト）
├── HYBRID_DESIGN.md              ← admin自動降格アーキテクチャ設計ドキュメント
├── CLAUDE.md                     ← このファイル
├── netlify.toml                  ← Netlify設定（Cache-Control: no-cache）
├── firebase.json                 ← Firebase CLI設定（firestoreルール参照）
├── firestore.rules               ← Firestoreセキュリティルール
├── .gitignore                    ← node_modules, app/, supabase/, .csv除外
├── .github/workflows/
│   ├── nightly-qa.yml            ← 毎晩JST 02:00 にClaudeでQA実行→issue自動作成
│   ├── monthly-refresh.yml       ← 毎月1日にPlaces APIでデータ更新（⚠️Issue #22: 承認フロー迂回）
│   └── nightly-cron.yml          ← 毎晩reports集計（Firestore読み取りのみ、課金なし）
├── scripts/                      ← 過去のaudit/fix/ingestスクリプト（Python/Node）
│   ├── fix_all_cities.py
│   ├── ingest_kobe.py
│   ├── monthly_refresh.js        ← monthly-refresh.ymlから呼ばれる（⚠️Issue #21: totalNew常に0）
│   ├── reports_aggregate.js      ← nightly-cron.ymlから呼ばれる
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
| CSS | 17-590 | 全スタイル（シート, マーカー, フィルター, 3タップレビュー等） |
| HTML | 595-720 | DOM構造（#map, #bottom, #sheet, picker, nudge） |
| L10N | 725-828 | JP/EN翻訳辞書 |
| CITIES | 829-845 | 都市設定（座標, bbox, 旗, 多言語名）15都市 |
| Firebase init | 851-861 | firebase.initializeApp, Firestore接続テスト |
| addUIOverlays | 878-918 | lang-toggle, adminモード（5タップ起動） |
| TIER_CONFIG | 971-998 | brands, types, colors, display設定 |
| tierKey() | ~1003-1030 | Tier判定ロジック（JP/US分岐, majorTerminals）⚠️Issue #24 |
| makeIcon/cluster | ~1031-1070 | マーカーアイコン・クラスター生成 |
| refreshZoom() | ~1079-1155 | マーカー描画（viewport/cluster切替, isRefreshingガード） |
| loadCity() | 1180-1256 | Firestore chunk並列fetch, キャッシュ(v6), withTimeout |
| renderCity() | ~1280-1350 | allMarkers生成, applyFilter, renderNearby |
| renderNearby() | ~1355-1440 | 近傍リスト（searchPin/GPS起点, stageExpand） |
| openDetail() | 1543-1614 | 詳細シート（顔emoji, 投票数, phraseCard, nav/rptボタン） |
| answerQ1/Q2/Q3 | 1616-1677 | 3タップレビュー（localStorage制限, reviews+reviewSummaries保存）⚠️Issue #27 |
| nav/nudge | 1712-1740 | Googleマップナビ, 帰宅後レビュー促進 |
| submitAdd | 1790-1840 | トイレ追加（admin直接 or pending+EmailJS） |
| startInlineReview/submitReview | 1899-1955 | ⚠️ デッドコード（#inline-reviewがDOM非存在, autoReview未使用）Issue #28参照 |
| switchTab() | 2014-2044 | タブ切替（Near Me時にGPS都市へリセット） |
| goToSearchResult() | 1976-2012 | 検索結果へ地図移動（switchTab呼ばずUIタブのみ更新）Issue #26 |
| searchCity() | 2049-2101 | Google Places Text Search (New API, locationBias無し) |
| init() | 2180-2225 | 起動フロー（geolocation, loadCity, invalidateSize, visitor counter） |

## Firestore構造

```
oasis-bde20/
├── cities/{cityKey}/chunks/{0-14}  ← トイレデータ本体（15都市 × 最大15chunk）
├── reviews/{docId}                 ← 3タップレビュー（access/refused/closed/cleanliness/paperSpace）
├── reviewSummaries/{toiletId}      ← 集計（access, refused, closed のincrement）
├── reports/{docId}                 ← 問題報告（reason, toiletId, reportedAt）
├── pending_toilets/{docId}         ← ユーザー追加申請（status: pending/approved）
└── stats/visitors                  ← 訪問者カウンター（total, today, lastDate）
```

## 既知バグ（Open Issues 早見表）

| Issue | 優先度 | 概要 |
|---|---|---|
| #9 | Critical | Firestore `allow write: if true` — 全データ誰でも改ざん可 |
| #5 | High | Google Places APIキーが index.html にハードコード |
| #4 | High | admin.htmlにAdminパスワード平文ハードコード |
| #11 | High | init() GPS race condition — 東京ユーザーがManhattanを見る可能性 |
| #28 | High | startInlineReview/submitReview がデッドコード, nudgeReview機能しない |
| #27 | High | answerQ3() でlocalStorage記録がFirestore書き込み前（失敗時に再投票不可） |
| #6,10,13,19 | High | XSS: 複数箇所でFirestore/APIデータをsanitizeせずinnerHTMLに挿入 |
| #7,8,14 | Medium | loadCity/goToSearchResult: try-catch欠如でローディング永久表示 |
| #16 | Medium | submitAdd() 失敗時も「✅追加完了」UIが表示される |
| #22 | Medium | monthly-refresh.yml がCLAUDE.mdのコスト承認フローを迂回して毎月自動実行 |
| #23 | Medium | me-dot（現在地ピン）がトイレピンの後ろに隠れる（zIndexOffset未設定） |
| #24 | Medium | subway_station が T1 に誤分類 |
| #25 | Medium | 「今すぐ入れる」フィルタが営業時間を考慮しない |
| #15 | Low | console.log('[CHECK]') デバッグコードが本番残存 |
| #26 | Low | searchPin が2用途で使い回される設計の脆弱性（TechDebt） |
| #29 | Low | nightly-qa.yml が index.html の末尾31行を読み飛ばす |
