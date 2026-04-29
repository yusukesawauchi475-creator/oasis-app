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
├── index.html                    ← 本番SPA（2,236行）。Leaflet地図+全UIロジック
├── admin.html                    ← 管理ダッシュボード（508行）。pending承認/reviews/自動降格管理
├── manifest.json                 ← PWA manifest
├── oasis-logo.jpg                ← アプリロゴ（favicon, apple-touch-icon）
├── OASIS_SSOT.md                 ← 引き継ぎドキュメント（SSOT）
├── HYBRID_DESIGN.md              ← ハイブリッドアーキテクチャ設計ドキュメント
├── CLAUDE.md                     ← このファイル
├── netlify.toml                  ← Netlify設定（Cache-Control: no-cache）
├── firebase.json                 ← Firebase CLI設定（firestoreルール参照）
├── firestore.rules               ← Firestoreセキュリティルール
├── .gitignore                    ← node_modules, app/, supabase/, .csv除外
├── docs/                         ← 設計思想・監査チェックリスト・ポストモーテム
│   ├── PHILOSOPHY_README.md
│   ├── audit-checklist.md
│   ├── core-philosophy.md
│   ├── handoff-template.md
│   └── post-mortems/             ← 障害・哲学違反の記録
├── scripts/                      ← audit/fix/ingestスクリプト（Python/Node）
│   ├── monthly_refresh.js        ← 月次Places APIインジェスト（要コスト承認）
│   ├── reports_aggregate.js      ← 夜間reports集計（Firestoreのみ、課金なし）
│   ├── ingest_kobe.py / ingest_lodging.py
│   ├── fix_all_cities.py / fix_*.py
│   ├── audit_*.py / audit_*.mjs
│   └── package.json              ← firebase-admin依存
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

## 対応都市（CITIES config、index.html L829-845）

| cityKey | 都市名 | 地域 |
|---|---|---|
| manhattan | New York | US |
| london | London | EU |
| sydney | Sydney | AU |
| melbourne | Melbourne | AU |
| brisbane | Brisbane | AU |
| tokyo | Tokyo | JP |
| osaka | Osaka | JP |
| kobe | Kobe | JP |
| fukuoka | Fukuoka | JP |
| sapporo | Sapporo | JP |
| nagoya | Nagoya | JP |
| kyoto | Kyoto | JP |
| hiroshima | Hiroshima | JP |
| naha | Naha | JP |
| kagoshima | Kagoshima | JP |

## 主要コンポーネント（index.html内）

| セクション | 行範囲(概算) | 内容 |
|---|---|---|
| CSS | 17-590 | 全スタイル（シート, マーカー, フィルター, 投票等） |
| HTML | 595-720 | DOM構造（#map, #bottom, #sheet, picker, nudge） |
| L10N | 725-828 | JP/EN翻訳辞書 |
| CITIES config | 829-845 | 15都市の座標・bbox・フラグ定義 |
| Firebase init | 851-861 | firebase.initializeApp, Firestore接続（起動時ヘルスチェック含む※Issue #30） |
| addUIOverlays | 878-919 | lang-toggle, adminモード |
| initMap() | 920-966 | Leaflet地図初期化（※Issue #15のデバッグconsole.log残存） |
| TIER_CONFIG | 971-1002 | brands, types, colors, display設定 |
| tierKey() | 1003-1035 | Tier判定ロジック（JP/US分岐, transitTypes） |
| makeIcon/cluster | 1037-1053 | マーカーアイコン生成 |
| applyFilter/refreshZoom | 1082-1175 | フィルタ適用, マーカー描画（viewport/cluster切替） |
| loadCity() | 1180-1265 | Firestore chunk並列fetch, キャッシュ(v5), loadKey管理 |
| renderCity() | 1296-1345 | allMarkers生成, applyFilter, renderNearby |
| distance helpers | 1328-1347 | distMeters(), fmtDist()（徒歩時間計算） |
| renderNearby() | 1374-1440 | 近傍リスト（searchPin/GPS起点, stageExpand） |
| selectCity() | 1444-1490 | 都市切り替え（searchPin設置, loadCity呼び出し） |
| goToMe() | 1492-1545 | GPS現在地取得・表示 |
| openDetail() | 1548-1624 | 詳細シート（3-tap review, 距離表示, Googleナビ） |
| answerQ1/Q2/Q3 | 1625-1720 | 3タップレビューシステム（※Issue #27のlocalStorage順序バグ） |
| submitAdd() | 1796-1815 | トイレ追加（admin直接 or pending+EmailJS） |
| adminDirectAdd() | 1817-1843 | 管理者直接追加（chunk選択, Firestore書き込み） |
| notifyNew* | 1850-1935 | EmailJS通知（notifyNewToilet/notifyNewReview） |
| submitReview() | 1937-1980 | ※デッドコード（Issue #28）。到達不能 |
| goToSearchResult() | 1982-2052 | 検索結果に飛ぶ（map.setView, searchPin設置） |
| searchCity() | 2055-2183 | Google Places Autocomplete + 都市ショートカット |
| init() | 2186-2231 | 起動フロー（geolocation race condition※Issue #11, loadCity） |

## Firestore構造

```
oasis-bde20/
├── cities/{cityKey}/chunks/{0-14}  ← トイレデータ本体
├── reviews/                        ← 星評価・投票・詳細レビュー
├── reviewSummaries/{toiletId}      ← 集計（ratingTotal, access, refused等）
├── reports/                        ← 問題報告
└── pending_toilets/                ← ユーザー追加申請（status: pending/approved）
```
