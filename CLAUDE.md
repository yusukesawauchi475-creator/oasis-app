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
~/Oasis/                          ← Git root, Netlifyデプロイ元（oasis-app）
├── index.html                    ← 本番SPA（2,250行）。Leaflet地図+全UIロジック
├── admin.html                    ← 管理画面（25,344bytes）パスワード保護
├── manifest.json                 ← PWAマニフェスト
├── oasis-logo.jpg                ← アプリロゴ（favicon, apple-touch-icon）
├── OASIS_SSOT.md                 ← 引き継ぎドキュメント（SSOT, v4.4）
├── OASIS_QA.md                   ← QAチェックリスト10項目
├── HYBRID_DESIGN.md              ← ハイブリッドデータアーキテクチャ設計書
├── CLAUDE.md                     ← このファイル
├── netlify.toml                  ← Netlify設定（Cache-Control: no-cache）
├── firebase.json                 ← Firebase CLI設定（firestoreルール参照）
├── firestore.rules               ← Firestoreセキュリティルール
├── .gitignore                    ← node_modules, app/, supabase/, .csv除外
├── .github/
│   └── workflows/
│       ├── nightly-qa.yml        ← 毎日JST 02:00 Claude QAレポート自動化
│       ├── nightly-cron.yml      ← 毎日JST 03:00 reports_aggregate.js実行
│       └── monthly-refresh.yml  ← 毎月1日JST 03:00 新規place追加
├── docs/                         ← Philosophyフレームワーク文書
│   ├── core-philosophy.md        ← 6原則
│   ├── audit-checklist.md        ← 5軸auditチェックリスト
│   ├── handoff-template.md
│   ├── PHILOSOPHY_README.md
│   └── post-mortems/             ← 障害ポストモーテム
├── scripts/                      ← audit/fix/ingestスクリプト（Python/Node）
│   ├── fix_all_cities.py
│   ├── fix_bbox_lodging.py
│   ├── fix_t4_promote.py
│   ├── fix_tier3.py
│   ├── ingest_kobe.py
│   ├── ingest_lodging.py
│   ├── monthly_refresh.js        ← 月次place追加（GitHub Actions実行）
│   ├── reports_aggregate.js      ← 報告集計・自動Tier4降格
│   ├── audit_*.py / audit_*.mjs  ← 各種audit
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

## 主要コンポーネント（index.html内）※ 2,250行、2026-05-01時点

| セクション | 行範囲(実測) | 内容 |
|---|---|---|
| CSS | 26-590 | 全スタイル（シート, マーカー, フィルター, 投票等） |
| HTML | 595-728 | DOM構造（#map, #bottom, #sheet, picker, nudge, cp-grid） |
| L10N | 733-815 | JP/EN翻訳辞書（walkMin関数含む） |
| CITIES | 829-845 | 15都市定義（座標・bbox・フラグ） |
| Firebase init | 851-861 | firebase.initializeApp, Firestore接続, 起動時ヘルスチェック |
| initMap() | 920-966 | Leaflet地図初期化, zoomend/moveend/click handler |
| addUIOverlays | 878-891 | lang-toggle, applyLang |
| Admin mode | 893-918 | handleAdminTap, updateAdminUI (5回タップで起動) |
| TIER_CONFIG | 971-997 | brands(dead code), types(dead code), colors, display設定 |
| tierKey() | 1005-1009 | Tier判定（Firestoreの tier フィールド優先→decideTierLocal） |
| decideTierLocal() | 1011-1049 | ブランド/タイプ/地域別Tier判定（単一ソース） |
| makeIcon/cluster | 1051-1067 | マーカーアイコン生成 |
| distMeters/fmtDist | 1342-1361 | ハーバーサイン距離計算・徒歩時間フォーマット |
| getOriginLatLng() | 1378-1386 | searchPin→GPS→都市中心の距離起点取得 |
| refreshZoom() | 1105-1190 | マーカー描画（viewport/cluster切替, isRefreshingガード） |
| loadCity() | 1194-1292 | Firestore chunk並列fetch, キャッシュ(v6), currentLoadKey競合防止 |
| renderCity() | 1310-1340 | allMarkers生成, applyFilter, renderNearby |
| renderNearby() | 1388-1460 | 近傍リスト（searchPin/GPS起点, stageExpand, fmtDist） |
| selectCity() | 1458-1505 | 都市切替（searchPin都市中心設置, loadCity） |
| goToMe() | 1506-1535 | 現在地取得（clearSearchPin→flyTo→renderNearby） |
| openDetail() | 1562-1634 | 詳細シート（顔, 3問投票, 距離表示, 3Dボタン） |
| answerQ1/Q2/Q3 | 1639-1697 | 3問タップ式レビュー（Q1:入可否→Q2:清潔→Q3:紙・広さ） |
| startInlineReview | 1919-1949 | インラインレビュー（到達不能デッドコード、issue #28） |
| submitReview | 1951-1980 | 詳細レビュー送信 |
| submitAdd | 1810-1917 | トイレ追加（admin直接 or pending+EmailJS） |
| goToSearchResult | 1996-2032 | 検索結果ピン設置・都市切替・UI更新 |
| switchTab() | 2034-2068 | Near Me/Search タブ切替（activeCity復元含む） |
| searchCity | 2069-2128 | Google Places Text Search (New) API呼出し |
| renderInlineLegend | 2129-2165 | 凡例インライン描画（5色） |
| applyLang() | 2178-2195 | UI翻訳適用（HUD都市名は未対応、issue #33） |
| init() | 2200-2249 | 起動フロー（geolocation, loadCity, 訪問者カウンター） |

## Firestore構造

```
oasis-bde20/
├── cities/{cityKey}/chunks/{0-14}  ← トイレデータ本体
├── reviews/                        ← 星評価・投票・詳細レビュー
├── reviewSummaries/{toiletId}      ← 集計（ratingTotal, access, refused等）
├── reports/                        ← 問題報告
└── pending_toilets/                ← ユーザー追加申請（status: pending/approved）
```
