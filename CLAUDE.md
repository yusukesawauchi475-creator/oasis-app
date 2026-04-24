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
  - 1セッション最大5 deploys
  - デプロイ前にコード確認必須
  - 同じエラーで3回失敗したらアプローチ変更、デプロイ停止
  - エラーが出ても即デプロイしない。原因特定してから1発で直す

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
~/oasis-app/                      ← Git root（ローカル: /home/user/oasis-app）, Netlifyデプロイ元
├── index.html                    ← 本番SPA（~2,207行）。Leaflet地図+全UIロジック
├── admin.html                    ← 管理ダッシュボード（ダッシュボード/申請/レビュー/自動降格タブ）
├── manifest.json                 ← PWAマニフェスト（name, icons, start_url等）
├── oasis-logo.jpg                ← アプリロゴ（favicon, apple-touch-icon）
├── OASIS_SSOT.md                 ← 引き継ぎドキュメント（SSOT）
├── OASIS_QA.md                   ← 定期QAチェックリスト（11項目）
├── HYBRID_DESIGN.md              ← ハイブリッドアーキテクチャ設計ドキュメント（参考用）
├── CLAUDE.md                     ← このファイル
├── netlify.toml                  ← Netlify設定（Cache-Control: no-cache）
├── firebase.json                 ← Firebase CLI設定（firestoreルール参照）
├── firestore.rules               ← Firestoreセキュリティルール（要修正: Issue #9）
├── .gitignore                    ← node_modules, app/, supabase/, .csv除外
├── .github/workflows/
│   ├── nightly-cron.yml          ← 毎日JST03:00: reports_aggregate.js 実行
│   └── monthly-refresh.yml      ← 毎月1日JST03:00: monthly_refresh.js 実行（Places API課金注意: Issue #22）
├── scripts/                      ← audit/fix/ingest/cronスクリプト（Python/Node）
│   ├── monthly_refresh.js        ← 月次Places API新規スポット取得（GitHub Actions用）
│   ├── reports_aggregate.js      ← 夜間レポート集計（GitHub Actions用）
│   ├── fix_all_cities.py
│   ├── ingest_kobe.py
│   └── ...（audit_*.py, fix_*.py 等）
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
| L10N | 738-816 | JP/EN翻訳辞書 |
| Firebase init | 851-877 | firebase.initializeApp, Firestore接続 |
| addUIOverlays | 878-919 | lang-toggle, adminモード（5回タップでadmin） |
| initMap() | 920-966 | Leaflet初期化, クラスタータップ処理 |
| TIER_CONFIG | 971-1004 | brands, types, colors, display設定 |
| tierKey() | 1005-1036 | Tier判定ロジック（JP/US分岐, majorTerminals） |
| makeIcon/cluster | 1037-1054 | マーカーアイコン生成 |
| refreshZoom() | 1090-1155 | マーカー描画（viewport/cluster切替, isRefreshingガード） |
| loadCity() | 1178-1253 | Firestore chunk並列fetch, キャッシュ(v5) |
| loadPendingToilets() | 1254-1291 | pending_toilets取得・マーカー追加 |
| renderCity() | 1292-1323 | allMarkers生成, applyFilter, renderNearby |
| renderNearby() | 1370-1437 | 近傍リスト（searchPin/GPS起点, stageExpand） |
| selectCity() | 1438-1461 | 都市ピッカー選択処理 |
| goToMe() | 1470-1500 | GPS現在地取得・都市切替 |
| openDetail() | 1526-1601 | 詳細シート（3-question tap review, 投票） |
| answerQ1/2/3 | 1602-1660 | 3択タップレビュー（入れた/断られた/閉鎖中 + コメント） |
| submitAdd | 1773-1826 | トイレ追加（admin直接 or pending+EmailJS） |
| notifyNewToilet/Review | 1827-1881 | EmailJS通知送信 |
| startInlineReview | 1882-1913 | インラインレビューUI起動 |
| submitReview | 1914-1958 | 詳細レビュー送信（Firestore + notifyNewReview） |
| goToSearchResult | 1959-2023 | 検索結果へ移動（loadCity + map.setView） |
| searchCity | 2024-2134 | Google Places Autocomplete (New API) |
| applyLang() | 2135-2156 | 言語切替UI更新 |
| init() | 2157-2207 | 起動フロー（geolocation, loadCity, invalidateSize） |

## Firestore構造

```
oasis-bde20/
├── cities/{cityKey}/chunks/{0-14}  ← トイレデータ本体
├── reviews/                        ← 星評価・投票・詳細レビュー
├── reviewSummaries/{toiletId}      ← 集計（ratingTotal, access, refused等）
├── reports/                        ← 問題報告
└── pending_toilets/                ← ユーザー追加申請（status: pending/approved）
```
