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
├── index.html                    ← 本番SPA（~2,200行）。Leaflet地図+全UIロジック
├── admin.html                    ← 管理ダッシュボード（pending承認・レビュー管理・自動降格確認）
├── oasis-logo.jpg                ← アプリロゴ（favicon, apple-touch-icon）
├── manifest.json                 ← PWAマニフェスト（スタンドアロン表示設定）
├── OASIS_SSOT.md                 ← 引き継ぎドキュメント（SSOT）
├── OASIS_QA.md                   ← デプロイ前QAチェックリスト（10項目）
├── HYBRID_DESIGN.md              ← ハイブリッドマップ設計ドキュメント
├── CLAUDE.md                     ← このファイル
├── netlify.toml                  ← Netlify設定（Cache-Control: no-cache）
├── firebase.json                 ← Firebase CLI設定（firestoreルール参照）
├── firestore.rules               ← Firestoreセキュリティルール
├── .gitignore                    ← node_modules, app/, supabase/, .csv除外
├── .github/workflows/            ← GitHub Actions ワークフロー
│   ├── monthly-refresh.yml       ← 月次Places APIインジェスト（毎月1日自動実行 ※Issue #22）
│   ├── nightly-cron.yml          ← 夜間reports集計（Firestoreリードのみ、課金なし）
│   └── nightly-qa.yml            ← 夜間QA自動チェック
├── scripts/                      ← audit/fix/ingestスクリプト（Python/Node）
│   ├── monthly_refresh.js        ← 月次Refresh本体（Places API呼び出し）
│   ├── reports_aggregate.js      ← reports集計スクリプト（nightly-cronから呼ばれる）
│   ├── ingest_kobe.py            ← 神戸データインジェスト
│   ├── ingest_lodging.py         ← ホテル・宿泊施設インジェスト
│   ├── fix_all_cities.py         ← 全都市データ一括修正
│   ├── fix_manhattan.py          ← Manhattan データ修正
│   ├── fix_bbox_lodging.py       ← BBoxロジック修正
│   ├── fix_t4_promote.py         ← Tier4プロモート処理
│   ├── fix_tier3.py              ← Tier3修正
│   ├── audit_direct.mjs          ← 直接auditスクリプト
│   ├── audit_final.py            ← 最終audit（Python）
│   ├── audit_gcloud.py           ← GCloud経由audit
│   ├── audit_manhattan.py        ← Manhattan専用audit
│   ├── audit_manhattan_node.mjs  ← Manhattan audit（Node版）
│   ├── audit_rest.py             ← REST audit
│   ├── audit_with_auth.mjs       ← 認証付きaudit
│   ├── package.json              ← scripts/ のNode依存（firebase-admin等）
│   └── package-lock.json
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
| CSS | 17-590 | 全スタイル（シート, マーカー, フィルター, 投票等） |
| HTML | 595-720 | DOM構造（#map, #bottom, #sheet, picker, nudge） |
| L10N | 725-810 | JP/EN翻訳辞書 |
| Firebase init | 850-865 | firebase.initializeApp, Firestore接続 |
| addUIOverlays | 879-920 | lang-toggle, adminモード |
| TIER_CONFIG | 969-994 | brands, types, colors, display設定 |
| tierKey() | 1003-1025 | Tier判定ロジック（JP/US分岐, majorTerminals） |
| makeIcon/cluster | 1027-1040 | マーカーアイコン生成 |
| refreshZoom() | 1079-1145 | マーカー描画（viewport/cluster切替, isRefreshingガード） |
| loadCity() | 1160-1210 | Firestore chunk並列fetch, キャッシュ(v5) |
| renderCity() | 1215-1245 | allMarkers生成, applyFilter, renderNearby |
| renderNearby() | 1290-1330 | 近傍リスト（searchPin/GPS起点, stageExpand） |
| openDetail() | 1375-1455 | 詳細シート（星, 顔, 投票, 3Dボタン） |
| rateStar/quickVote | 1457-1495 | 星評価・投票（localStorage制限, reviewSummaries） |
| submitReview | 1610-1640 | 詳細レビュー送信 |
| submitAdd | 1640-1720 | トイレ追加（admin直接 or pending+EmailJS） |
| searchCity | 1895-1950 | Google Places Autocomplete (New) |
| goToPlaceId | 1952-1970 | Place Details → goToSearchResult |
| init() | 2035-2070 | 起動フロー（geolocation, loadCity, invalidateSize） |

## 主要コンポーネント（admin.html内）

| セクション | 内容 |
|---|---|
| 認証 | ADMIN_PW平文チェック + localStorage `adminAuth` フラグ（⚠️ Issue #4） |
| loadPending() | pending_toilets一覧・承認・却下（⚠️ Issue #10 XSS未修正） |
| loadReviews() | reviews一覧・削除（⚠️ Issue #10 XSS未修正） |
| loadDowngraded() | 自動降格タブ（⚠️ Issue #19 XSS・Issue #20 Maps URL未修正） |
| 都市統計タブ | cities/{city}/chunks のTier別件数集計 |

## オープンIssue一覧（2026-04-25時点）

| # | 重要度 | タイトル（要約） |
|---|---|---|
| #22 | High | monthly-refresh.yml が CLAUDE.md コスト承認フローを迂回して自動実行 |
| #21 | Medium | monthly_refresh.js の totalNew カウンターが常に 0（splice後参照） |
| #20 | Low | admin.html loadDowngraded() 「地図で確認」リンクのURL形式誤り |
| #19 | High | admin.html loadDowngraded() — XSS（Issue #10 と同パターン） |
| #18 | Low | notifyNewReview() の .catch(() => {}) が空でエラー無音スキップ |
| #17 | Low | openDetail() reviews fetch の catch(e) {} が空 |
| #16 | Medium | submitAdd() — try-catch外で成功UIが表示されサイレントデータロスト |
| #15 | Low | initMap() に [CHECK] デバッグログが本番残存 |
| #14 | Medium | isLoadingCity ガードでローディングスピナーが残存・都市切替スキップ |
| #13 | High | renderNearbyCards/openDetail — t.name が非エスケープで XSS |
| #12 | Low | submitReview() — null チェック前に「ありがとう」UI表示 |
| #11 | High | init() geolocation race condition — GPS別都市検出時に地図が空 |
| #10 | Critical | admin.html — ユーザー投稿データをサニタイズなしで innerHTML に挿入 |
| #9 | Critical | Firestore rules が `allow write: if true` — 全データが誰でも改ざん可能 |
| #8 | Medium | goToSearchResult() — loadCity エラー未キャッチでローディング無限表示 |
| #7 | Medium | loadCity() — Promise.all に try-catch なし → spinner永久表示 |
| #6 | High | searchCity() — Places APIレスポンスを innerHTML に直接挿入（XSS） |
| #5 | High | Google Places API Key が index.html にハードコード |
| #4 | Critical | admin.html に Admin パスワードが平文ハードコード |
| #3 | Low | localStorage キャッシュ書き込み失敗が無音スキップ |
| #2 | Medium | Firebase 書き込みの .catch(() => {}) がエラーを握りつぶし |

## Firestore構造

```
oasis-bde20/
├── cities/{cityKey}/chunks/{0-14}  ← トイレデータ本体
├── reviews/                        ← 星評価・投票・詳細レビュー
├── reviewSummaries/{toiletId}      ← 集計（ratingTotal, access, refused等）
├── reports/                        ← 問題報告
└── pending_toilets/                ← ユーザー追加申請（status: pending/approved）
```
