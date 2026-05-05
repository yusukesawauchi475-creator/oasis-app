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
├── admin.html                    ← 管理画面（~850行）。パスワード保護、申請/レビュー管理
├── manifest.json                 ← PWA manifest（アイコン, テーマカラー等）
├── oasis-logo.jpg                ← アプリロゴ（favicon, apple-touch-icon）
├── OASIS_SSOT.md                 ← 引き継ぎドキュメント（SSOT）
├── OASIS_QA.md                   ← 毎晩実行するQAチェックリスト（11項目）
├── HYBRID_DESIGN.md              ← ハイブリッドデータアーキテクチャ設計書
├── CLAUDE.md                     ← このファイル
├── netlify.toml                  ← Netlify設定（Cache-Control: no-cache）
├── firebase.json                 ← Firebase CLI設定（firestoreルール参照）
├── firestore.rules               ← Firestoreセキュリティルール
├── .gitignore                    ← node_modules, app/, supabase/, .csv除外
├── .github/
│   └── workflows/
│       ├── nightly-qa.yml        ← 毎日JST 02:00 Claude APIでQAレポート・issue化
│       ├── nightly-cron.yml      ← 毎日JST 03:00 reports集計→自動Tier4降格
│       └── monthly-refresh.yml  ← 毎月1日JST 03:00 新規place追加
├── docs/                         ← Philosophy framework（Humプロジェクトから移植）
│   ├── core-philosophy.md        ← 6原則
│   ├── audit-checklist.md        ← 5軸auditチェックリスト
│   ├── handoff-template.md       ← セッション引き継ぎテンプレート
│   ├── PHILOSOPHY_README.md
│   └── post-mortems/             ← 過去障害の振り返り
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
├── lib/
│   └── tier_logic.js             ← Tier判定ロジック（ingest用。frontendとは別管理）
└── package.json                  ← firebase-admin依存

~/Downloads/OASIS_SSOT.md         ← SSOTのバックアップ（Downloads内）
```

## 主要コンポーネント（index.html内）

※ 2026-05-05 現在。index.html は **2,250行**。コード変更のたびにずれるため概算で参照すること。

| セクション | 行範囲(概算) | 内容 |
|---|---|---|
| CSS | 26-636 | 全スタイル（シート, マーカー, フィルター, 投票等） |
| HTML | 638-732 | DOM構造（#map, #bottom, #sheet, picker, nudge） |
| L10N | 733-813 | JP/EN翻訳辞書（85キー、ja/en完全一致） |
| CITIES | 829-845 | 15都市定義（center, zoom, bbox） |
| Firebase init | 851-861 | firebase.initializeApp, Firestoreヘルスチェック |
| addUIOverlays | 878-919 | lang-toggle, adminモード（5回タップ起動） |
| TIER_CONFIG | 971-999 | brands, types, colors, display設定 |
| tierKey()/decideTierLocal() | 1005-1050 | Tier判定（保存tier優先→localフォールバック, JP/US/UK/AU分岐） |
| makeIcon/clusterIcon | 1051-1080 | マーカー・クラスタアイコン生成 |
| applyFilter/refreshZoom() | 1096-1170 | フィルター適用・マーカー描画（viewport/cluster切替） |
| loadCity() | 1194-1270 | Firestore chunk並列fetch, キャッシュ(v6), currentLoadKeyガード |
| loadPendingToilets() | 1272-1293 | pending_toilets fetch・bbox絞り込み |
| renderCity() | 1310-1323 | allMarkers生成, applyFilter, renderNearby |
| renderNearby() | 1388-1452 | 近傍リスト（searchPin/GPS起点, stageExpand, expandNearby） |
| selectCity() | 1458-1483 | 都市選択→flyTo→loadCity |
| goToMe() | 1506-1535 | GPS取得→detectCity→flyTo |
| openDetail() | 1562-1633 | 詳細シート（顔アイコン, 投票数, 3Dボタン） |
| answerQ1/Q2/Q3() | 1639-1697 | 3問タップ式レビュー→Firestore書き込み→localStorage制限 |
| navWithNudge/nudge | 1740-1763 | ルート案内→帰還時nudge→レビュー促進 |
| submitReport() | 1772-1788 | reports コレクション書き込み |
| submitAdd() | 1810-1829 | トイレ追加（admin直接 or pending+EmailJS） |
| startInlineReview/submitReview | 1919-1979 | 詳細レビュー（⚠️ dead code: inline-review要素なし） |
| goToSearchResult() | 1996-2032 | 検索結果→detectCity→loadCity→searchPin配置 |
| switchTab() | 2034-2068 | Near Me/Searchタブ切替 |
| searchCity() | 2069-2121 | Google Places Text Search (New), ローカル都市ショートカット併用 |
| renderInlineLegend() | 2126-2141 | 凡例（T2_MINUS欠落: issue #40） |
| init() | 2200-2247 | 起動フロー（geolocation, loadCity, 訪問者カウンター） |

## Firestore構造

```
oasis-bde20/
├── cities/{cityKey}/chunks/{0-14}  ← トイレデータ本体（15都市、合計~41,580件）
├── reviews/{reviewId}              ← 3問タップ式レビュー（access/refused/closed/cleanliness/paperSpace）
├── reviewSummaries/{toiletId}      ← 集計（total, access, refused, closed）
├── reports/{reportId}              ← 問題報告（toiletId, reason）
├── pending_toilets/{docId}         ← ユーザー追加申請（status: pending/approved）
└── stats/visitors                  ← 訪問者カウンター（total, today, lastDate）
```
