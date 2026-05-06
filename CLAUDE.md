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
├── admin.html                    ← 管理者パネル（pending_toilets承認、downgraded確認等）
├── manifest.json                 ← PWA manifest（ホーム画面追加対応）
├── oasis-logo.jpg                ← アプリロゴ（favicon, apple-touch-icon）
├── OASIS_SSOT.md                 ← 引き継ぎドキュメント（SSOT）
├── HYBRID_DESIGN.md              ← ハイブリッド設計ドキュメント
├── CLAUDE.md                     ← このファイル
├── netlify.toml                  ← Netlify設定（Cache-Control: no-cache）
├── firebase.json                 ← Firebase CLI設定（firestoreルール参照）
├── firestore.rules               ← Firestoreセキュリティルール
├── .gitignore                    ← node_modules, app/, supabase/, .csv除外
├── .github/
│   └── workflows/
│       ├── nightly-qa.yml        ← 毎晩のQA自動実行
│       ├── nightly-cron.yml      ← 夜間cronジョブ
│       └── monthly-refresh.yml  ← 月次Placesデータ更新（⚠️コスト承認必須）
├── docs/                         ← ドキュメント群
│   ├── core-philosophy.md        ← 設計哲学
│   ├── audit-checklist.md        ← 監査チェックリスト
│   ├── handoff-template.md       ← 引き継ぎテンプレート
│   ├── PHILOSOPHY_README.md      ← 哲学README
│   └── post-mortems/             ← 障害ポストモーテム
├── scripts/                      ← audit/fix/ingestスクリプト（Python/Node）
│   ├── monthly_refresh.js        ← 月次更新スクリプト本体
│   ├── fix_all_cities.py
│   ├── fix_bbox_lodging.py
│   ├── fix_manhattan.py
│   ├── fix_t4_promote.py
│   ├── fix_tier3.py
│   ├── ingest_kobe.py
│   ├── ingest_lodging.py
│   ├── reports_aggregate.js
│   ├── audit_direct.mjs / audit_final.py / audit_*.py/mjs
│   └── package.json              ← scripts/配下のNode依存
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
| CSS | 26-636 | 全スタイル（シート, マーカー, フィルター, 投票等） |
| HTML | 638-732 | DOM構造（#map, #bottom, #sheet, picker, nudge） |
| L10N + setLang | 738-820 | JP/EN翻訳辞書, tr()関数, setLang() |
| Firebase init | 851-861 | firebase.initializeApp, Firestore接続 |
| addUIOverlays | 878-919 | lang-toggle, adminモード（5回タップで解除） |
| TIER_CONFIG | 971-996 | brands, types, colors, display設定 |
| tierKey() | 1005-1050 | Tier判定ロジック（JP/US分岐, majorTerminals） |
| makeIcon/clusterIcon | 1051-1093 | マーカー・クラスターアイコン生成 |
| applyFilter() | 1096-1104 | フィルター適用（すべて/今すぐ入れる） |
| refreshZoom() | 1105-1193 | マーカー描画（viewport/cluster切替, isRefreshingガード） |
| loadCity() | 1194-1309 | Firestore chunk並列fetch, キャッシュ(v5), loadPendingToilets |
| renderCity() | 1310-1387 | allMarkers生成, applyFilter, renderNearby |
| renderNearby/Cards | 1388-1457 | 近傍リスト（searchPin/GPS起点, stageExpand） |
| selectCity() | 1458-1505 | 都市切替 |
| goToMe() | 1506-1536 | GPS現在地移動 |
| detectCity() | 1537-1561 | 座標→都市キー判定 |
| openDetail() | 1562-1638 | 詳細シート表示（トイレ情報, 投票フロー呼び出し） |
| answerQ1/Q2/Q3 | 1639-1809 | 3段階投票（入れた/清潔度/紙）, localStorage制限 |
| submitAdd() | 1810-1863 | トイレ追加（admin直接 or pending+EmailJS） |
| notifyNewToilet/Review | 1864-1918 | EmailJS通知 |
| startInlineReview() | 1919-1950 | インラインレビュー開始（※openDetail未接続のデッドコード） |
| submitReview() | 1951-1995 | 詳細レビュー送信 |
| goToSearchResult() | 1996-2068 | 検索結果座標→loadCity→マーカー |
| searchCity() | 2069-2125 | Google Places Autocomplete (New) |
| renderInlineLegend() | 2126-2166 | 地図凡例描画 |
| showLoading/hideLoading | 2167-2177 | ローディングUI |
| applyLang() | 2178-2199 | 言語切替UI一括更新 |
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
