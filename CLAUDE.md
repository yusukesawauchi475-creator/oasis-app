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
├── admin.html                    ← 管理画面（約680行）
├── oasis-logo.jpg                ← アプリロゴ（favicon, apple-touch-icon）
├── manifest.json                 ← PWA manifest
├── OASIS_SSOT.md                 ← 引き継ぎドキュメント（SSOT）
├── OASIS_QA.md                   ← 夜間QAプロンプト（11項目）
├── HYBRID_DESIGN.md              ← ハイブリッド設計ドキュメント
├── CLAUDE.md                     ← このファイル
├── netlify.toml                  ← Netlify設定（Cache-Control: no-cache）
├── firebase.json                 ← Firebase CLI設定（firestoreルール参照）
├── firestore.rules               ← Firestoreセキュリティルール
├── .gitignore                    ← node_modules, app/, supabase/, .csv除外
├── docs/                         ← 設計・哲学ドキュメント
│   ├── PHILOSOPHY_README.md
│   ├── audit-checklist.md
│   ├── core-philosophy.md
│   ├── handoff-template.md
│   └── post-mortems/
├── scripts/                      ← audit/fix/ingestスクリプト（Python/Node）
│   ├── fix_all_cities.py
│   ├── ingest_kobe.py
│   ├── monthly_refresh.js
│   ├── audit_*.py / audit_*.mjs  ← 各種auditスクリプト
│   ├── fix_*.py                  ← データ修正スクリプト
│   └── package.json / package-lock.json
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

実際の行番号（2026-05-20 確認済み、全2,250行）

| セクション | 行範囲 | 内容 |
|---|---|---|
| CSS | 17-590 | 全スタイル（シート, マーカー, フィルター, 投票等） |
| HTML | 595-737 | DOM構造（#map, #bottom, #sheet, picker, nudge） |
| L10N | 738-813 | JP/EN翻訳辞書 |
| Firebase init | 851-877 | firebase.initializeApp, Firestore接続 |
| addUIOverlays | 878-940 | lang-toggle, adminモード |
| TIER_CONFIG | 971-996 | brands, types, colors, display設定 |
| tierKey() | 1005-1049 | Tier判定ロジック（JP/US分岐, majorTerminals） |
| scoreToilets() | 1069-1093 | ※デッドコード（issue #47）TIER_WEIGHTも同様 |
| applyFilter() | 1096-1102 | フィルター適用→refreshZoom+renderNearby |
| makeIcon/cluster | 1051-1067 | マーカーアイコン生成 |
| refreshZoom() | 1105-1192 | マーカー描画（viewport/cluster切替, isRefreshingガード） |
| loadCity() | 1194-1270 | Firestore chunk並列fetch, キャッシュ(v5) |
| loadPendingToilets() | 1272-1308 | pending_toilets fetch（cityKeyフィルターなし: issue #43） |
| renderCity() | 1310-1337 | allMarkers生成, applyFilter, renderNearby |
| renderNearby() | 1388-1409 | 近傍リスト（searchPin/GPS起点, stageExpand） |
| renderNearbyCards() | 1421-1438 | 近傍カード描画 |
| expandNearby() | 1441-1453 | 「もっと見る」展開（最大20件）|
| setFilter() | 1498-1501 | フィルターUI + applyFilter呼び出し |
| selectCity() | 1458-1480 | 都市選択（issue #61: activeFilterリセットなし） |
| goToMe() | 1506-1534 | 現在地GPS取得・me-dot描画 |
| detectCity() | 1537-1560 | GPS座標→activeCity自動判定 |
| openDetail() | 1562-1634 | 詳細シート（投票表示, 3Dボタン, reviewsフェッチ） |
| 3-Question Review | 1639-1697 | answerQ1/Q2/Q3（旧rateStar/quickVoteを置換） |
| submitAdd() | 1810-1829 | トイレ追加（admin直接 or pending+EmailJS） |
| adminDirectAdd() | 1831-1917 | admin直接追加（chunk逐次fetch: issue #51） |
| startInlineReview() | 1919-1950 | ※デッドコード（issue #28） |
| submitReview() | 1951-1994 | インラインレビュー送信 |
| goToSearchResult() | 1996-2031 | 検索結果座標へ移動+loadCity |
| switchTab() | 2034-2067 | タブ切替（near/search） |
| searchCity() | 2069-2121 | Google Places Text Search API（XSS: issue #64） |
| renderInlineLegend() | 2126-2142 | 凡例描画（T2_MINUS省略: issue #40） |
| showLoading/hideLoading | 2167-2168 | ローディング表示制御 |
| applyLang() | 2178-2198 | 言語切替UI更新（placeholder未更新: issue #60） |
| init() | 2200-2250 | 起動フロー（geolocation, loadCity, invalidateSize） |

## Firestore構造

```
oasis-bde20/
├── cities/{cityKey}/chunks/{0-14}  ← トイレデータ本体
├── reviews/                        ← 星評価・投票・詳細レビュー
├── reviewSummaries/{toiletId}      ← 集計（ratingTotal, access, refused等）
├── reports/                        ← 問題報告
└── pending_toilets/                ← ユーザー追加申請（status: pending/approved）
```
