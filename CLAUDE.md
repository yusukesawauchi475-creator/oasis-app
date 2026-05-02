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

1. OASIS_QA.md の11項目全チェック
2. 実機動作想定シミュレーション：
   - 全ボタンのonclick接続確認
   - 前進/戻る動作の整合性
   - JP/ENモードでの全画面チェック
   - ローディング・エラーハンドリング
3. 問題があればseverity付きでリストアップ
4. 修正案を提示（実行はオーナー承認後）

QAは「言われなくてもやる」ことが前提。
OASIS_QA.md のセクション数は **11項目**（1〜11）。

## ファイル構成

```
~/Oasis/                          ← Git root, Netlifyデプロイ元
├── index.html                    ← 本番SPA（~2,250行）。Leaflet地図+全UIロジック
├── admin.html                    ← 管理パネル（パスワード保護、3タブ: ダッシュボード/申請/レビュー）
├── oasis-logo.jpg                ← アプリロゴ（favicon, apple-touch-icon）
├── manifest.json                 ← PWA manifest
├── OASIS_SSOT.md                 ← 引き継ぎドキュメント（SSOT）
├── HYBRID_DESIGN.md              ← ハイブリッドアーキテクチャ Phase 1/2 設計文書
├── CLAUDE.md                     ← このファイル
├── OASIS_QA.md                   ← 夜間QAプロンプト（11項目）
├── netlify.toml                  ← Netlify設定（Cache-Control: no-cache）
├── firebase.json                 ← Firebase CLI設定（firestoreルール参照）
├── firestore.rules               ← Firestoreセキュリティルール
├── .gitignore                    ← node_modules, app/, supabase/, .csv除外
├── docs/                         ← Philosophy framework（Hum project から移植）
│   ├── core-philosophy.md        ← 6原則
│   ├── audit-checklist.md        ← 5軸audit
│   ├── handoff-template.md
│   ├── PHILOSOPHY_README.md
│   └── post-mortems/             ← バグ事後分析
├── scripts/                      ← audit/fix/ingestスクリプト（Python/Node）
│   ├── fix_all_cities.py
│   ├── ingest_kobe.py
│   ├── monthly_refresh.js        ← 月次新規place追加（GitHub Actions経由）
│   ├── reports_aggregate.js      ← 3件報告で自動Tier4降格（GitHub Actions経由）
│   └── ...（audit_*.py/mjs, fix_*.py 多数）
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

| セクション | 行範囲(実測) | 内容 |
|---|---|---|
| CSS | 17-590 | 全スタイル（シート, マーカー, フィルター, 投票等） |
| HTML | 595-720 | DOM構造（#map, #bottom, #sheet, picker, nudge） |
| L10N + CITIES | 738-845 | JP/EN翻訳辞書 + 15都市定義（center/bbox/zoom） |
| Firebase init | 851-870 | firebase.initializeApp, Firestore接続 |
| addUIOverlays | 878-970 | lang-toggle, adminモード（5回タップ） |
| TIER_CONFIG | 971-1003 | brands, types, colors, display設定（⚠️ brands/typesはデッドコード #35） |
| tierKey() / decideTierLocal() | 1005-1050 | Tier判定ロジック（JP/US分岐, majorTerminals） |
| makeIcon/cluster | 1051-1090 | マーカーアイコン生成 |
| applyFilter / refreshZoom() | 1096-1190 | フィルター + マーカー描画（viewport/cluster切替, isRefreshingガード） |
| loadCity() | 1194-1300 | Firestore chunk並列fetch, キャッシュ(oasis_v6_*) |
| renderCity() | 1310-1365 | allMarkers生成, applyFilter, renderNearby |
| renderNearby() | 1388-1460 | 近傍リスト（searchPin/GPS起点, stageExpand） |
| selectCity() / updateHud() | 1458-1500 | 都市切替, HUD更新 |
| openDetail() | 1562-1638 | 詳細シート（顔アイコン, 3問タップレビュー, 投票件数, 3Dボタン） |
| answerQ1/Q2/Q3 | 1639-1700 | 3問タップ式レビュー（⭐星評価は削除済み） |
| submitAdd() / notifyNewToilet() | 1810-1895 | トイレ追加（admin直接 or pending+EmailJS） |
| submitReview() / notifyNewReview() | 1951-1995 | レビュー送信 + EmailJS通知 |
| goToSearchResult() / switchTab() | 1996-2068 | 検索結果表示, タブ切替 |
| searchCity() | 2069-2125 | Google Places Text Search (New) |
| applyLang() | 2178-2195 | 言語適用（⚠️ updateHud未呼び出し #33） |
| init() | 2200-2250 | 起動フロー（geolocation, loadCity, invalidateSize） |

## Firestore構造

```
oasis-bde20/
├── cities/{cityKey}/chunks/{0-14}  ← トイレデータ本体（⚠️ allow write: if true #36）
├── reviews/                        ← 3問タップ式レビュー（create only）
├── reviewSummaries/{toiletId}      ← 集計（access/refused/closed）（⚠️ allow update: if true #38）
├── reports/                        ← 問題報告（create only）
├── pending_toilets/                ← ユーザー追加申請（⚠️ allow update: if true #37）
└── stats/visitors                  ← 訪問者カウンター（total/today/lastDate）
```
