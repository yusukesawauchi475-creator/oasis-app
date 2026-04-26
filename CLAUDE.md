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
├── index.html                    ← 本番SPA（~2,500行）。Leaflet地図+全UIロジック
├── admin.html                    ← 管理画面（ダッシュボード/申請/レビュー/自動降格タブ）
├── oasis-logo.jpg                ← アプリロゴ（favicon, apple-touch-icon）
├── manifest.json                 ← PWAマニフェスト（name/icons/display設定）
├── OASIS_SSOT.md                 ← 引き継ぎドキュメント（SSOT）
├── OASIS_QA.md                   ← QAチェックリスト10項目
├── HYBRID_DESIGN.md              ← ハイブリッドデータアーキテクチャ設計（Phase 1/2）
├── CLAUDE.md                     ← このファイル
├── netlify.toml                  ← Netlify設定（Cache-Control: no-cache）
├── firebase.json                 ← Firebase CLI設定（firestoreルール参照）
├── firestore.rules               ← Firestoreセキュリティルール
├── .gitignore                    ← node_modules, app/, supabase/, .csv, *.key除外
├── .github/workflows/
│   ├── nightly-qa.yml            ← 毎日JST 02:00 Claude APIでQAレポート+issue自動化
│   ├── nightly-cron.yml          ← 毎日JST 03:00 reports_aggregate.js（3件報告でT4降格）
│   └── monthly-refresh.yml      ← 毎月1日JST 03:00 monthly_refresh.js（Places新規追加）
├── scripts/                      ← audit/fix/ingest/cron スクリプト（Python/Node）
│   ├── reports_aggregate.js      ← nightly-cron用: 3件以上報告→自動Tier4降格
│   ├── monthly_refresh.js        ← monthly-refresh用: Google Places新規place追加
│   ├── fix_all_cities.py
│   ├── ingest_kobe.py
│   ├── package.json              ← firebase-admin依存（scripts/用）
│   └── ...（audit_*.py, fix_*.py等）
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
| CSS | 17-600 | 全スタイル（シート, マーカー, フィルター, 3問レビュー等） |
| HTML | 605-730 | DOM構造（#map, #bottom, #sheet, picker, nudge） |
| L10N | 735-820 | JP/EN翻訳辞書（78キー） |
| Firebase init | 855-870 | firebase.initializeApp, Firestore接続 |
| addUIOverlays | 885-930 | lang-toggle, adminモード（5回タップ起動） |
| TIER_CONFIG | 975-1000 | brands, types, colors, display設定 |
| tierKey() | 1005-1035 | Tier判定ロジック（JP/US分岐, majorTerminals） |
| makeIcon/cluster | 1037-1055 | マーカーアイコン生成, me-dot, searchPin |
| refreshZoom() | 1085-1155 | マーカー描画（viewport/cluster切替, isRefreshingガード） |
| loadCity() | 1165-1225 | Firestore chunk並列fetch, currentLoadKey, キャッシュ(v6) |
| renderCity() | 1230-1260 | allMarkers生成, applyFilter, renderNearby |
| renderNearby() | 1300-1355 | 近傍リスト（getOriginLatLng/searchPin優先, stageExpand） |
| selectCity() | 1360-1395 | 都市ショートカット選択, 都市中心searchPin設定 |
| openDetail() | 1400-1480 | 詳細シート（顔アイコン, 3問タップ, 投票数, 3Dボタン） |
| quickVote/answerQ | 1482-1560 | 3問タップ式レビュー（Q1/Q2/Q3, localStorage制限） |
| submitReview | 1620-1660 | 詳細テキストレビュー送信, notifyNewReview |
| submitAdd | 1660-1740 | トイレ追加（admin直接 or pending+EmailJS） |
| switchTab() | 1820-1870 | タブ切替（Near Me時にactiveCity/searchPin復元） |
| searchCity() | 1920-1985 | Google Places Text Search (New), 都市ショートカット併合表示 |
| goToSearchResult() | 1988-2040 | 検索結果→loadCity→map.setView, currentLoadKeyリセット |
| init() | 2100-2150 | 起動フロー（geolocation, detectCity, loadCity, invalidateSize） |

## Firestore構造

```
oasis-bde20/
├── cities/{cityKey}/chunks/{0-14}  ← トイレデータ本体（全15都市, 約41,580件）
├── reviews/                        ← 3問タップ投票・詳細テキストレビュー
├── reviewSummaries/{toiletId}      ← 集計（access, refused, closed, cleanliness, paperSpace）
├── reports/                        ← 問題報告（3件以上でnightly-cronがT4自動降格）
├── pending_toilets/                ← ユーザー追加申請（status: pending/approved）
└── stats/
    ├── visitors                    ← 訪問者カウンター（total/today/lastDate）
    └── autoDowngraded/history      ← 自動降格履歴（admin.html「自動降格」タブで表示）
```
