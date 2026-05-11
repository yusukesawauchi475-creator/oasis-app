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
├── admin.html                    ← 管理者パネル（~510行）。pending承認・Tier確認
├── manifest.json                 ← PWA Web App Manifest
├── oasis-logo.jpg                ← アプリロゴ（favicon, apple-touch-icon）
├── OASIS_SSOT.md                 ← 引き継ぎドキュメント（SSOT）
├── OASIS_QA.md                   ← 夜間QAチェックリスト（11項目）
├── HYBRID_DESIGN.md              ← ハイブリッド設計ドキュメント
├── CLAUDE.md                     ← このファイル
├── netlify.toml                  ← Netlify設定（Cache-Control: no-cache）
├── firebase.json                 ← Firebase CLI設定（firestoreルール参照）
├── firestore.rules               ← Firestoreセキュリティルール
├── .gitignore                    ← node_modules, app/, supabase/, .csv除外
├── .github/workflows/
│   ├── monthly-refresh.yml       ← 月次Places APIリフレッシュ（毎月1日JST03:00）
│   ├── nightly-cron.yml          ← 夜間reportsアグリゲーション（毎日JST03:00）
│   └── nightly-qa.yml            ← 夜間QAチェック（毎日JST02:00）
├── docs/
│   ├── PHILOSOPHY_README.md
│   ├── audit-checklist.md
│   ├── core-philosophy.md
│   ├── handoff-template.md
│   └── post-mortems/
├── scripts/                      ← audit/fix/ingestスクリプト（Python/Node）
│   ├── audit_direct.mjs
│   ├── audit_final.py
│   ├── audit_gcloud.py
│   ├── audit_manhattan.py
│   ├── audit_manhattan_node.mjs
│   ├── audit_rest.py
│   ├── audit_with_auth.mjs
│   ├── fix_all_cities.py
│   ├── fix_bbox_lodging.py
│   ├── fix_manhattan.py
│   ├── fix_t4_promote.py
│   ├── fix_tier3.py
│   ├── ingest_kobe.py
│   ├── ingest_lodging.py
│   ├── monthly_refresh.js        ← GitHub Actions から呼ばれる月次リフレッシュ
│   ├── reports_aggregate.js      ← GitHub Actions から呼ばれる夜間アグリゲーション
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

~/Downloads/OASIS_SSOT.md         ← SSOTのバックアップ（Downloads内）
```

## 主要コンポーネント（index.html内）

| セクション | 行範囲(概算) | 内容 |
|---|---|---|
| CSS | 26-635 | 全スタイル（シート, マーカー, フィルター, 投票等） |
| HTML | 638-728 | DOM構造（#map, #bottom, #sheet, picker, nudge） |
| L10N | 738-816 | JP/EN翻訳辞書 |
| CITIES定義 | 829-845 | 15都市（JP10 + NY/London/Sydney/Melbourne/Brisbane） |
| Firebase init | 851-877 | firebase.initializeApp, Firestore接続, 起動テスト |
| addUIOverlays/admin | 878-968 | lang-toggle, adminモード（5回タップ） |
| TIER_CONFIG | 969-1002 | brands, types, colors, display設定 |
| tierKey()/decideTierLocal() | 1005-1050 | Tier判定ロジック（JP/US/UK/AU分岐, majorTerminals） |
| makeIcon/cluster/markers | 1051-1094 | マーカーアイコン生成・追加・クリア |
| applyFilter()/refreshZoom() | 1096-1170 | フィルター適用, マーカー描画（viewport/cluster切替） |
| loadCity() | 1194-1270 | Firestore chunk並列fetch, キャッシュ(v6) |
| loadPendingToilets() | 1272-1309 | pending_toilets fetch・マーカー追加 |
| renderCity() | 1310-1341 | allMarkers生成, applyFilter |
| stageExpand/renderNearby() | 1366-1457 | 近傍リスト（searchPin/GPS起点, 段階展開） |
| selectCity()/updateHud() | 1458-1493 | 都市選択, HUD更新 |
| goToMe()/detectCity() | 1506-1547 | GPS現在地取得, 都市自動検出 |
| openDetail() | 1562-1634 | 詳細シート（顔, 投票カウント, 3Dボタン） |
| 3Q Review system | 1636-1980 | answerQ1-3, submitReview（localStorage制限） |
| nav/navWithNudge/nudge | 1732-1764 | Google Maps案内, レビュー促進nudge |
| openReport/submitReport | 1765-1788 | 問題報告（reportsコレクション） |
| openAddToilet/submitAdd | 1789-1863 | トイレ追加（admin直接 or pending+EmailJS） |
| notifyNewToilet/Review | 1864-1918 | EmailJS通知 |
| startInlineReview/submitReview | 1919-1980 | インラインレビュー（nudge経由） |
| clearSearchPin/nearestCity | 1981-1994 | 検索ピンクリア, 最近傍都市検索 |
| goToSearchResult() | 1996-2032 | 検索結果→都市loadCity→マップ移動 |
| switchTab() | 2034-2064 | Near Me/検索タブ切替, 都市復元 |
| searchCity() | 2069-2121 | Google Places Text Search（New API） |
| renderInlineLegend() | 2126-2142 | 凡例描画（T1/T2_PLUS/T3/T4/PARTNER） |
| openPicker/closePicker | 2147-2162 | 都市ピッカー |
| showLoading/hideLoading | 2167-2173 | ローディングオーバーレイ制御 |
| applyLang() | 2178-2195 | 言語切替後のUI文字列更新 |
| init() | 2200-2246 | 起動フロー（geolocation, loadCity, 訪問者カウント） |

## Firestore構造

```
oasis-bde20/
├── cities/{cityKey}/chunks/{0-14}  ← トイレデータ本体
├── reviews/                        ← 投票・詳細レビュー（3Q方式）
├── reviewSummaries/{toiletId}      ← 集計（access, refused, closed件数）
├── reports/                        ← 問題報告
├── pending_toilets/                ← ユーザー追加申請（status: pending/approved）
└── stats/visitors                  ← 訪問者カウンター（total, today, lastDate）
```
