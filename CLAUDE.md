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
├── index.html                    ← 本番SPA（2,250行）。Leaflet地図+全UIロジック
├── admin.html                    ← 管理者ページ（508行）。審査・ダウングレード管理
├── manifest.json                 ← PWAマニフェスト
├── oasis-logo.jpg                ← アプリロゴ（favicon, apple-touch-icon）
├── OASIS_SSOT.md                 ← 引き継ぎドキュメント（SSOT）
├── OASIS_QA.md                   ← QAチェックリスト（10項目）
├── HYBRID_DESIGN.md              ← ハイブリッド設計ドキュメント
├── CLAUDE.md                     ← このファイル
├── netlify.toml                  ← Netlify設定（Cache-Control: no-cache）
├── firebase.json                 ← Firebase CLI設定（firestoreルール参照）
├── firestore.rules               ← Firestoreセキュリティルール
├── .gitignore                    ← node_modules, app/, supabase/, .csv除外
├── docs/                         ← 設計哲学・ポストモーテム・監査チェックリスト
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

## 主要コンポーネント（index.html内、2,250行）

| セクション | 行範囲(概算) | 内容 |
|---|---|---|
| CSS | 17-636 | 全スタイル（シート, マーカー, フィルター, 投票等） |
| HTML | 638-728 | DOM構造（#map, #bottom, #sheet, picker, nudge） |
| Firebase CDN | 729-731 | firebasejs 9.22.0 / Leaflet 1.9.4 スクリプトタグ |
| L10N | 738-813 | JP/EN翻訳辞書 |
| Firebase init | 851-865 | firebase.initializeApp, Firestore接続, ヘルスチェック |
| addUIOverlays | 878-895 | lang-toggle, adminモード |
| initMap() | 920-970 | Leafletマップ初期化, zoomend/moveendイベント |
| TIER_CONFIG | 971-997 | brands, types, colors, display設定 |
| tierKey() / decideTierLocal() | 1005-1050 | Tier判定ロジック（JP/US分岐, majorTerminals） |
| makeIcon / clusterIcon | 1051-1080 | マーカーアイコン生成 |
| addMarker / clearMarkers | 1081-1104 | マーカー追加・全削除 |
| applyFilter() | 1096-1104 | フィルター適用（T1/T2/全件） |
| refreshZoom() | 1105-1170 | マーカー描画（viewport/cluster切替, isRefreshingガード） |
| restoreSearchPin() | 1171-1186 | 検索ピン復元 |
| loadCity() | 1194-1271 | Firestore chunk並列fetch, キャッシュ(v5), cancel対応 |
| loadPendingToilets() | 1272-1295 | pending_toilets fetch・マーカー追加 |
| addPendingMarker() | 1296-1309 | pendingトイレのマーカー生成 |
| renderCity() | 1310-1325 | allMarkers生成, applyFilter, renderNearby |
| distMeters / fmtDist | 1342-1365 | 距離計算・フォーマット |
| stageExpand() | 1366-1387 | 近傍リスト段階展開ロジック |
| renderNearby() | 1388-1457 | 近傍リスト（searchPin/GPS起点, stageExpand） |
| selectCity() | 1458-1484 | 都市切替（キャンセル前城ロード, HUD更新） |
| goToMe() | 1506-1536 | GPS現在地移動 |
| detectCity() | 1537-1547 | 緯度経度→都市キー推定 |
| openDetail() | 1562-1638 | 詳細シート（顔, 投票, アクセス情報, ナビボタン） |
| answerQ1 / Q2 / Q3 | 1639-1698 | アクセス・個室・紙評価投票（localStorage制限） |
| navWithNudge() | 1740-1764 | ナビ起動＋ nudge 表示 |
| nudgeReview() | 1756-1764 | ナビ後レビュー誘導 |
| openReport / submitReport | 1765-1788 | 問題報告 |
| submitAdd() | 1810-1830 | トイレ追加（pending+EmailJS） |
| adminDirectAdd() | 1831-1859 | admin直接追加（Firestore直書き） |
| notifyNewToilet / Review | 1864-1914 | EmailJS通知送信 |
| startInlineReview() | 1919-1950 | インラインレビューUI（3ステップ） |
| submitReview() | 1951-1980 | 詳細レビュー送信（Firestore + reviewSummaries） |
| goToSearchResult() | 1996-2033 | 検索結果ピン立て→loadCity→renderNearby |
| switchTab() | 2034-2065 | Near Me / Map タブ切替 |
| searchCity() | 2069-2125 | Google Places Text Search API 検索 |
| renderInlineLegend() | 2126-2146 | 地図凡例描画 |
| openPicker / closePicker | 2147-2166 | 都市ピッカーモーダル |
| applyLang() | 2178-2199 | 言語切替後UI一括更新 |
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
