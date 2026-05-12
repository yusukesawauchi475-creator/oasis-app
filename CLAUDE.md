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
~/Oasis/                          ← Git root, Netlifyデプロイ元（実際: ~/oasis-app/）
├── index.html                    ← 本番SPA（~2,250行）。Leaflet地図+全UIロジック
├── admin.html                    ← 管理者ダッシュボード（Tier確認, pending承認, レビュー管理）
├── manifest.json                 ← PWA manifest（ホーム画面追加対応）
├── oasis-logo.jpg                ← アプリロゴ（favicon, apple-touch-icon）
├── OASIS_SSOT.md                 ← 引き継ぎドキュメント（SSOT）
├── OASIS_QA.md                   ← デプロイ前QAチェックリスト（10項目）
├── HYBRID_DESIGN.md              ← ハイブリッド設計ドキュメント
├── CLAUDE.md                     ← このファイル
├── netlify.toml                  ← Netlify設定（Cache-Control: no-cache）
├── firebase.json                 ← Firebase CLI設定（firestoreルール参照）
├── firestore.rules               ← Firestoreセキュリティルール
├── .gitignore                    ← node_modules, app/, supabase/, .csv除外
├── docs/                         ← 設計哲学・チェックリスト・引き継ぎテンプレート
│   ├── PHILOSOPHY_README.md
│   ├── core-philosophy.md
│   ├── audit-checklist.md
│   ├── handoff-template.md
│   └── post-mortems/             ← インシデント事後分析
│       └── 2026-04-28_philosophy-violation.md
├── .github/workflows/            ← GitHub Actions
│   ├── nightly-qa.yml            ← 毎夜QA自動実行（Claude API呼び出し）
│   ├── nightly-cron.yml          ← 毎夜レポート集計（reports_aggregate.js）
│   └── monthly-refresh.yml      ← 毎月1日Places API再インジェスト（⚠️要承認）
├── scripts/                      ← audit/fix/ingestスクリプト（Python/Node）
│   ├── fix_all_cities.py
│   ├── fix_bbox_lodging.py
│   ├── fix_manhattan.py
│   ├── fix_t4_promote.py
│   ├── fix_tier3.py
│   ├── ingest_kobe.py
│   ├── ingest_lodging.py
│   ├── monthly_refresh.js        ← Places API再インジェスト本体
│   ├── reports_aggregate.js      ← レポート集計
│   ├── audit_*.py / audit_*.mjs  ← 各種auditスクリプト
│   └── package.json
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
```

## 主要コンポーネント（index.html内）

※行番号は概算。コード変更のたびにずれる。grep/Read で都度確認推奨。

| セクション | 行範囲(概算) | 内容 |
|---|---|---|
| CSS | 26-636 | 全スタイル（シート, マーカー, フィルター, 投票等） |
| HTML | 638-732 | DOM構造（#map, #bottom, #sheet, picker, nudge） |
| L10N / LANG | 733-828 | JP/EN翻訳辞書（L10N）、LANG変数、setLang() |
| CITIES / Firebase init | 829-869 | 15都市定義 + firebase.initializeApp, Firestore接続 |
| addUIOverlays | 878-919 | lang-toggle, adminモード, handleAdminTap() |
| initMap() | 920-969 | Leaflet地図初期化, イベントリスナー設定 |
| TIER_CONFIG | 971-999 | brands, types, colors, display設定 |
| tierKey() / decideTierLocal() | 1005-1050 | Tier判定ロジック（JP/US/UK/AU分岐, region-aware） |
| makeIcon/clusterIcon | 1051-1068 | マーカーアイコン生成 |
| scoreToilets() | 1069-1079 | ※デッドコード（issue #47）。呼ばれていない |
| refreshZoom() | 1105-1170 | マーカー描画（zoom≥14個別/未満クラスター, isRefreshingガード） |
| loadCity() | 1194-1271 | Firestore chunk並列fetch, キャッシュ(v5) |
| loadPendingToilets() | 1272-1308 | admin用pendingマーカー取得 |
| renderCity() | 1310-1323 | allMarkers生成, applyFilter, renderNearby |
| renderNearby() | 1388-1452 | 近傍リスト（searchPin/GPS起点, stageExpand） |
| selectCity() / updateHud() | 1458-1503 | 都市切替, HUD更新 |
| goToMe() | 1506-1536 | GPS現在地取得 |
| openDetail() | 1562-1638 | 詳細シート（Tier badge, 顔, 投票ボタン, navBtn） |
| answerQ1/Q2/Q3 | 1639-1697 | 3タップレビューシステム（localStorage制限, reviewSummaries） |
| nav() / navWithNudge() | 1732-1763 | ナビゲーション + nudgeセット |
| submitAdd() / adminDirectAdd() | 1810-1863 | トイレ追加（admin直接 or pending+EmailJS） |
| startInlineReview() / submitReview() | 1919-1979 | ※デッドコード（issue #28）。nudgeReviewから到達不可 |
| goToSearchResult() | 1996-2032 | 検索結果座標 → loadCity + マーカー配置 |
| switchTab() | 2034-2067 | Near Me/Search タブ切替 |
| searchCity() | 2069-2125 | Google Places Autocomplete (New) + 都市ショートカット |
| renderInlineLegend() | 2126-2145 | 凡例描画（T2_MINUS欠落 issue #40） |
| applyLang() | 2178-2198 | 言語切替後のUI更新（HUD未更新 issue #33） |
| init() | 2200-2247 | 起動フロー（geolocation, loadCity, 訪問者カウンター） |

## Firestore構造

```
oasis-bde20/
├── cities/{cityKey}/chunks/{0-14}  ← トイレデータ本体
├── reviews/                        ← 星評価・投票・詳細レビュー
├── reviewSummaries/{toiletId}      ← 集計（ratingTotal, access, refused等）
├── reports/                        ← 問題報告
└── pending_toilets/                ← ユーザー追加申請（status: pending/approved）
```
