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
├── admin.html                    ← 管理者UI（~508行）。トイレ承認・ダウングレード確認
├── oasis-logo.jpg                ← アプリロゴ（favicon, apple-touch-icon）
├── manifest.json                 ← PWAマニフェスト
├── OASIS_SSOT.md                 ← 引き継ぎドキュメント（SSOT）
├── HYBRID_DESIGN.md              ← ハイブリッドデザイン設計ドキュメント
├── CLAUDE.md                     ← このファイル
├── OASIS_QA.md                   ← QAチェックリスト（10項目）
├── netlify.toml                  ← Netlify設定（Cache-Control: no-cache）
├── firebase.json                 ← Firebase CLI設定（firestoreルール参照）
├── firestore.rules               ← Firestoreセキュリティルール
├── .gitignore                    ← node_modules, app/, supabase/, .csv除外
├── docs/                         ← 設計ドキュメント
│   ├── PHILOSOPHY_README.md
│   ├── audit-checklist.md
│   ├── core-philosophy.md
│   ├── handoff-template.md
│   └── post-mortems/
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
└── package.json                  ← firebase-admin依存

~/Downloads/OASIS_SSOT.md         ← SSOTのバックアップ（Downloads内）
```

## 主要コンポーネント（index.html内）

| セクション | 行範囲 | 内容 |
|---|---|---|
| CSS | 17-590 | 全スタイル（シート, マーカー, フィルター, 投票等） |
| HTML | 595-720 | DOM構造（#map, #bottom, #sheet, picker, nudge） |
| L10N | 725-815 | JP/EN翻訳辞書 |
| CITIES | 829-845 | 15都市定義（bbox, center, zoom）。kagoshima含む |
| Firebase init | 851-861 | firebase.initializeApp, Firestore接続, 起動テスト |
| STATE | 866-873 | map, allMarkers, allToilets, userLat/Lng等グローバル変数 |
| addUIOverlays | 878-918 | lang-toggle, adminモード (handleAdminTap, updateAdminUI) |
| initMap() | 920-968 | Leaflet地図初期化, click/zoom/moveendイベント |
| TIER_CONFIG | 971-1002 | brands(未使用), types(未使用), colors, display設定 |
| tierKey/decideTierLocal | 1003-1067 | Tier判定ロジック（JP/US/UK/AU分岐）, makeIcon, clusterIcon |
| applyFilter/refreshZoom | 1096-1179 | フィルター適用・マーカー描画（viewport/cluster切替） |
| loadCity() | 1194-1270 | Firestore chunk並列fetch, キャッシュ(v6) |
| loadPendingToilets | 1272-1308 | pending_toilets fetch・bbox絞り込み・マーカー追加 |
| renderCity() | 1310-1323 | clearMarkers→全マーカー再生成, applyFilter, renderNearby |
| renderNearby/expandNearby | 1366-1453 | 近傍リスト（searchPin/GPS起点, stageExpand, 最大20件） |
| selectCity/updateHud | 1458-1493 | 都市切替（searchPin=都市中心）, HUD更新 |
| goToMe/detectCity | 1506-1543 | 現在地取得, 都市自動検出（bbox判定） |
| openDetail() | 1562-1633 | 詳細シート（顔スコア, answerQ1/Q2/Q3投票UI, ナビボタン） |
| answerQ1/Q2/Q3 | 1636-1697 | 3ステップ投票（localStorage制限, reviewSummaries更新） |
| navWithNudge/nudge | 1728-1760 | ナビ起動, visibilitychange→帰還nudge（issue #53参照） |
| submitReport | 1772-1783 | 問題報告（reports コレクション） |
| submitAdd/adminDirectAdd | 1810-1857 | トイレ追加（admin直接 or pending+EmailJS通知） |
| startInlineReview/submitReview | 1919-1975 | インラインレビュー（到達不能デッドコード: issue #28） |
| goToSearchResult/switchTab | 1996-2064 | 検索結果移動, タブ切替（Near Me復帰でgoToMe） |
| searchCity | 2069-2121 | Google Places Text Search (New) API（500ms debounce） |
| renderInlineLegend | 2126-2142 | 凡例（T2_MINUSオレンジ欠落: issue #40） |
| openPicker/closePicker | 2147-2162 | 都市ピッカー |
| applyLang | 2178-2195 | UI文字列更新（HUD都市名は未更新: issue #33） |
| init() | 2200-2247 | 起動フロー（geolocation race condition: issue #11, 訪問者カウンター） |

## Firestore構造

```
oasis-bde20/
├── cities/{cityKey}/chunks/{0-14}  ← トイレデータ本体
├── reviews/                        ← 星評価・投票・詳細レビュー
├── reviewSummaries/{toiletId}      ← 集計（ratingTotal, access, refused等）
├── reports/                        ← 問題報告
└── pending_toilets/                ← ユーザー追加申請（status: pending/approved）
```
