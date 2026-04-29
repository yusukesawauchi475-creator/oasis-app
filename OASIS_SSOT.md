# OASIS APP — SSOT / 引き継ぎドキュメント

## ハンドオフ合言葉
「SSOT読んで。Oasis appのCTO頼む。」

---

## 基本情報

| 項目 | 値 |
|---|---|
| 本番URL | https://findoasis.app |
| Netlify URL | https://idyllic-mooncake-b78e56.netlify.app |
| Firebase project | oasis-bde20 |
| Firebase API Key | index.html 埋め込み（ブラウザ用、HTTP referrer制限未設定・TODO） |
| Google Places API Key（ブラウザ用） | index.html 埋め込み、oasis-app プロジェクト「Maps Platform API Key」、API制限: Places API/Places API(New)のみ |
| Google Places API Key（サーバー用） | GitHub Secrets `PLACES_API_KEY`、oasis-app プロジェクト「Places API - Server Side」 |
| Firebase Service Account | GitHub Secrets `FIREBASE_SA_KEY`、Key ID末尾 55e40fde77b5（旧鍵 c2b9abdc79a4 は2026-04-24削除済み） |
| Anthropic API Key | GitHub Secrets `ANTHROPIC_API_KEY`（nightly-qa.yml用） |

---

## Current state（2026-04-28 v4.4）

### データ
- 全15都市・約41,580件（Manhattan/London/Tokyo/Osaka/Kobe/Sydney/Melbourne/Brisbane/福岡/札幌/名古屋/京都/広島/那覇/鹿児島）
- Manhattan bbox拡張済み（Brooklyn/Queens/Jersey City含む、lng<-74.0で1,607件確認済）
- Firestoreチャンク構造: cities/{cityKey}/chunks/{0-14}
- isPartner:true は0件（IBD ingest未実行）
- pending_toilets: City Point Brooklyn → status:approved（chunk 11に追加済み）
- JP都市名日本語化: 7,600件変換済み（英語名73.4%→33.6%に改善）、残り6,434件は店名等でそのまま
- 鹿児島: 1,580件ingest済み（2026-04-23、コスト$0、JP名94.7%）
- 有料トイレ修正: free:false→null 8,691件一括更新。free===trueのみ「🆓無料」表示

### UI/UX実装済み
- TIER_CONFIG（brands/types/colors/display）
- Bottom tab 2枚（Near Me / Search）
- 段階展開（T1+T2P+PARTNER→T2M→T3→T4）
- フィルター：「すべて」「🩵今すぐ入れる」2つのみ（tier===1フィルタ）
- Tier色：T1=水色(#ADE8F4)、T2_PLUS=緑(#4CAF50)、T2_MINUS=オレンジ(#E67E22)、T3=黄、T4=赤（非表示）
- 詳細シート v3：顔アイコン(accessRate基準)、3問タップ式レビュー、投票件数表示(🚪🙅🔒)、3Dボタン
- 3問レビュー: Q1入れた/断られた/閉鎖中 → Q2清潔さ(きれい/普通/汚い) → Q3紙・広さ(紙あり+広い/紙のみ/紙なし・狭い)
- ⭐星評価: 削除済み（3問タップ式に完全移行）
- 詳細シートボタン: JP「📍ルート案内」「🚩報告」/ EN「📍Directions」「🚩Report」
- one-vote制限: localStorage `voted_${toiletId}` で重複防止
- reviewSummaries: answerQ3完了時にaccess/refused/closed を increment
- JP/ENトグル（localStorage保存、地図上部中央）
- L10N: 85キーJP/EN完全一致。pageTitle/adminAdded/noResults対応済み
- 赤rippleピン（現在地 me-dot divIcon）
- 検索結果ピン: L.marker divIcon ティアドロップ型（#FF3B30、zIndexOffset:9999）+ 300m薄円(searchArea)
- 検索時に都市ピルを「📍 場所名」に変更、クリア時に元の都市名に復帰
- 重複マーカー: 20px以内の重なり→リスト選択UI（spotsHere）
- フィルターボタンクリック時のsearchPin保護（map click bubbling防止）
- restoreSearchPin: remove→addTo方式、rAF/cluster両パス+applyFilter後300msで復元
- pending_toilets: 地図上に薄いマーカー(opacity:0.45)で表示、cityBbox内のみ
- EmailJS通知: 新規トイレ追加時にhello@findoasis.appへ承認/却下リンク付きメール送信
- adminモード: JP/ENトグル5回タップで起動、+ボタン赤化、chunk直接書込み
- Trader Joe's / Whole Foods / Target: T1_USブランドとしてT1に分類
- JPコンビニ（ファミマ/ローソン/セブン）: T2_PLUSに分類
- US小駅（subway/train）: T4（非表示）。majorTerminals（Penn/GC/PA/Union/MSG）はT1維持
- food_court: T2_PLUSに追加。shopping_mall: T2_PLUSから削除
- ロゴ差し替え（oasis-logo.jpg）
- ローディングblur reveal アニメーション
- 凡例：色ドット5個のみ→タップで展開（toggle式）
- 詳細シートoverflow-x:hidden + 施設名word-break
- オフライン時: 「接続できません。ネットワークを確認してください。」表示
- ルート案内: searchPinがある場合はsearchPin座標をorigin設定
- 距離表示: 60分超 or 10km超はkm表示に切替
- GPS未許可時のfallback: activeCity中心座標で距離計算
- OGタグ: description/title/image/url/type
- PWA: manifest.json + mobile-web-app-capable + apple-mobile-web-app-title
- 訪問者カウンター: stats/visitors（total/today/lastDate）
- レビュー通知メール: answerQ3完了時 → notifyNewReview() → EmailJS
- L10N: 78キーJP/EN完全一致（星評価キー削除、Q2/Q3キー追加）

### admin.html（findoasis.app/admin.html）
- パスワード保護: `oasis2024admin` → localStorage adminAuth
- 3タブ: ダッシュボード / 申請 / レビュー
- ダッシュボード: 総ロケーション / 総レビュー / 承認待ち(+承認/却下内訳) / 累計訪問者(+今日)
- レビューTOP5ランキング（トイレ名+maps link）
- 都市別カード: 件数+レビュー数 / T1件数+割合 / T4非表示件数
- 更新日時表示
- 申請タブ: pending_toilets一覧、承認→chunk追加+EmailJS通知、却下→status更新
- レビュータブ: トイレ名表示（chunkからID検索）、Google Mapsリンク、バッジ形式、コメント吹き出し、削除ボタン
- URLアクション: ?action=approve&id=XXX でメールから直接承認/却下
- tierKey()ロジックをindex.htmlと同一で複製

### 検索
- Google Places Text Search (New) `places.googleapis.com/v1/places:searchText`
- FieldMask: `places.displayName,places.formattedAddress,places.location`
- リクエスト: `languageCode:'ja'`, `regionCode:'JP'`, `maxResultCount:10`, `rankPreference:'RELEVANCE'`
- locationBias: 国全体rectangle（JP:24-46°N/122-146°E、US/UK/AU各国対応）
- 座標を直接取得（Place Details不要、1 API callで完結）
- detectCity null時は最近傍都市にfallback（nearestCity関数）
- 徒歩時間: searchPin優先→GPS→cityCenter（getOriginLatLng）
- **Nominatim廃止済み**、**Autocomplete→Text Search移行済み**

### EmailJS設定
- Service ID: `oasis_service`
- Template ID: `template_u1d9vhj`
- Public Key: `WUp_s87vWDzZhpmTv`
- 変数: toilet_name, toilet_lat, toilet_lng, toilet_note, city, reported_at, map_link
- 宛先: hello@findoasis.app
- 申請メールに承認/却下リンク付き（admin.html?action=approve&id=XXX）
- レビュー通知メール: [Oasis] 新規レビュー（トイレ名/評価/maps link）

### GitHub Actions
- nightly-qa.yml（既存）: 毎日JST 02:00、Claude APIでQAレポート、Critical/High自動issue化
- **nightly-cron.yml（2026-04-24追加）**: 毎日JST 03:00、reports_aggregate.js実行、3件以上の報告で自動Tier4降格
- **monthly-refresh.yml（2026-04-24追加）**: 毎月1日JST 03:00、monthly_refresh.js実行（15都市の新規place追加）、結果をGitHub Issue化
- Secrets: ANTHROPIC_API_KEY / FIREBASE_SA_KEY / PLACES_API_KEY
- 鍵の受け渡し方式: ファイル化ではなく`env:`経由（2026-04-24 Phase 1移行完了）

### パフォーマンス
- progressive loading: chunk 0先行表示→残り1-14並列fetch→各chunk完了時にaddMarker+refreshZoom
- `isLoadingCity` フラグで二重実行ガード
- `init()`: geolocation callback で別都市検出時は末尾の loadCity をスキップ
- `refreshZoom()`: `isRefreshing` + `refreshQueued` フラグで無限ループ・連打対応
- zoom>=14時のbounds取得を `requestAnimationFrame` で遅延
- viewport内のみマーカー描画（zoom>=14）、T4は常時非表示（bus_stop/lodging/POI-only含む）
- tier logic改善: bus_stop→T4、lodging→T4、POI単体→T4、T3からlodging除外
- 10都市動作シミュレーション検証済み（detectCity/loadCity/renderNearby/filter全OK）
- localStorageキャッシュ: `oasis_v6_*` キー（v5からバスト済み）
- 手動バックアップ: ~/oasis-ingest/backup.js → ~/oasis-backups/YYYY-MM-DD.json
- goToMe()冒頭でclearSearchPin()（周辺ボタンで検索ピンクリア）
- キャッシュ読み込み時 `Array.isArray(d) && d.length > 0` ガード
- emptyState発火条件: `toilets.length===0 && opts.fetchFailed`（chunk全失敗時のみ）
- 各chunkに10秒タイムアウト（withTimeout）

### Firestoreルール（2026-04-23更新・deploy済み）
- reviews: read+create、update/delete不可（削除はAdmin SDK経由）
- pending_toilets: read+create+update（承認用）、delete不可
- cities: read+write（承認chunk追加用）
- reports: read+create
- stats: read+create+update
- TODO: マーケ前にFirebase Auth導入してcustom claim admin判定に移行

### 残課題
**緊急（ユーザー影響、進行中）**
1. tier ロジック single source 化（ingest 時確定 → frontend は読むだけ）
2. ingest 系全 refactor（lib/ 共通モジュール化）
3. データ修復スクリプト（既存41,580件に primaryType 補完）

**データ improve 5案（並行進行、優先度順）**
1. 競合スクレイピング（OSM, 自治体オープンデータ）→ 神戸テスト中
2. 駅構内親子データ構造（IBD 差別化、5月本格着手）
3. レビューデータ逆引き enrichment
4. ユーザー新規追加機能
5. 営業時間 Places Detail enrichment（コスト ~$700、後回し）

**Phase 2: ~/oasis-ingest/ 27本のenv移行**(保留中)

**他の残課題**
- レビュースキーマ統一（quickVote vs submitReview）
- レビュー閲覧 Phase B/C
- index.html ブラウザ用Placesキー Application restrictions未設定
- admin dashboard map可視化
- Manhattan bbox拡張（Weehawken/Hoboken/Jersey City）
- Firebase Auth導入（マーケ開始前必須）
- I know IBD Partner ingest（2,884店舗）
- マーケ開始（JP: X/Twitter、US: Reddit IBD communities）
- 英語名残り6,434件の処理（優先度低）

### 完了済み（2026-04-28セッション）
**バグ修正（10+ commits、ユーザー影響）**
- searchPin 神戸11000km問題（loadCity競合バグ）→ cb3f23a, 06a476b, 6b1bcec
- 都市選択後の距離10000km再発 → 1d9d6d8
- 検索結果タップでNYCに飛び戻る → goToSearchResult から switchTab('near') 削除
- 神戸クラスタが3個しか出ない → cellSize 0.2→0.03度に細分化
- ズームアウトでパン後にクラスタ消える → moveend ハンドラの zoom>=14 ガード削除
- searchPin が他レイヤーに埋もれる → L.circleMarker → L.marker + zIndexOffset 10000

**Philosophy framework 導入（Hum project から移植）**
- docs/core-philosophy.md(6原則)
- docs/audit-checklist.md(5軸 audit)
- docs/handoff-template.md
- docs/PHILOSOPHY_README.md
- docs/post-mortems/ ディレクトリ

**データ品質 audit（重大な構造的バグ5件発見）**
- ingest tier ロジックと frontend tier ロジックの分離（地下鉄=T1 バグの根本）
- ingest 3スクリプトで FieldMask 不統一
- sim_cities.js bbox が古い
- CHUNK_SIZE 500 vs 800 不整合
- 重複排除が Place ID のみ

### 完了済み（2026-04-24セッション）

**セキュリティインシデント対応（完全クローズ）**
- 古いFirebase秘密鍵（c2b9abdc79a4）漏洩 → 無効化 → 新鍵（55e40fde77b5）にローテ → Google Cloud Consoleで旧鍵削除
- GitHub Secrets に FIREBASE_SA_KEY 登録、nightly-cron 手動実行で動作検証済
- Google Places APIキー分離：ブラウザ用（既存、API制限追加）+ サーバー用新規作成（GitHub Secrets PLACES_API_KEY）
- ブラウザ用キーに API restrictions 設定（Places API と Places API (New) のみ）
- monthly_refresh.js のハードコードAPIキー削除、env var必須化

**GitHub Actions自動化**
- nightly-cron.yml 新規: 毎日JST 03:00 reports_aggregate.js（3件報告で自動Tier4降格）
- monthly-refresh.yml 新規: 毎月1日JST 03:00 monthly_refresh.js（新規place追加、結果Issue化）
- 鍵渡し方式をファイル化からenv経由に統一（Phase 1: ~/Oasis/scripts/ 2本完了）

**admin.html 強化**
- 自動降格タブ追加（stats/autoDowngraded/history 表示、復元ボタン）
- ダッシュボードTOP5のトイレ名解決（Place IDむき出し問題解消）
- レビュータブのバッジ拡張（priv/paper/cleanliness/paperSpace 4種追加、CSS 4クラス）

**UI改善（index.html）**
- Kobe bbox西側拡張（須磨/垂水カバー、135.070→134.970）
- 検索結果住所プレフィックス除去（「日本、」「United States,」等）
- 「今すぐ入れる」フィルタが下部リストにも連動（applyFilter内でrenderNearby呼び出し追加）

**ドキュメント**
- HYBRID_DESIGN.md新規: ハイブリッドデータアーキテクチャ Phase 1/2 設計

**Near Me / 検索フロー一連バグ修正（午後）**
- ユーザー報告「検索→周辺タブで現在地に戻らない / 神戸検索が機能しない」を起点に、loadCity / switchTab / selectCity / goToSearchResult の状態管理 race condition を順次解消
- グローバル変数 currentLoadKey 導入で並行 loadCity を安全にキャンセル（旧 chunks 1-14 が新都市の allToilets を汚染しないよう、各 chunk 完了時に cityKey 一致チェック）
- selectCity 完了時の UI閉じ + 都市中心 searchPin で距離計算origin修正（`getOriginLatLng()` の優先順位 `searchPin > userLat/Lng > activeCity中心` を逆手に取る）
- 検索の locationBias 削除でグローバル検索化（NYCから神戸検索が1件しか返らない問題解消）
- 検索結果 onclick を data 属性経由に（特殊文字を含む name でもクリックで座標が壊れない）
- languageCode を UI言語トグル（LANG）に連動

**コミット履歴（2026-04-24）**
- 06baecf: cron基盤 + Phase 1書き換え
- b40fa81: workflow env修正 + ハードコード鍵削除
- 886c83d: Kobe bbox拡張 + 住所プレフィックス除去
- 9730c4e: admin自動降格タブ + HYBRID設計文書
- 2781b49: TOP5名前解決 + レビューバッジ拡張 + T1フィルタ連動 + SSOT v4.3更新
- 43190f4: switchTab('near') searchPin clear + flyTo（不完全、後続 cb3f23a で根本修正）
- b8548fd: 5-deploys-per-session ルール撤廃（CLAUDE.md + SSOT）
- 1b7b8d0: switchTab('near') に activeCity 切替追加（第2弾、競合バグ未解決）
- cb3f23a: loadCity 競合バグ根本修正（currentLoadKey 導入、第3弾）
- 06a476b: goToSearchResult にも同 race condition 対策
- 6b1bcec: selectCity + switchTab('near') 競合解消
- 1d9d6d8: selectCity で都市中心に searchPin → 距離計算origin修正
- c84ed8c: 検索で都市ショートカット + Places API 両方表示
- 000306e: locationBias 削除でグローバル検索化、languageCode 動的化
- 4442e87: 検索結果 onclick を data 属性方式化、座標破損バグ対策

### 完了済み（2026-04-23セッション）
- ~~3問タップ式レビュー~~ → 実装済み（⭐5評価削除、Q1/Q2/Q3）
- ~~レビュー通知メール~~ → notifyNewReview()実装済み
- ~~tier logic改善~~ → bus_stop/lodging/POI-only → T4
- ~~Firestoreルール強化~~ → delete全ブロック、deploy済み
- ~~backup.js~~ → ~/oasis-ingest/backup.js作成済み
- ~~鹿児島ingest~~ → 1,580件、コスト$0
- ~~検索範囲拡大~~ → 国全体rectangle + maxResultCount:10
- ~~有料トイレ修正~~ → free:false→null 8,691件
- ~~goToMe() clearSearchPin~~ → 追加済み
- ~~OGタグ更新~~ → 「トイレすぐそこに」
- ~~UI-Data整合性QA~~ → セクション11追加

---

## アーキテクチャ

**Firestore-first（Overpassはadmin ingest専用、user-facing一切なし）**

```
ユーザーが都市選択 / GPS自動検出
    ↓
localStorage 24hキャッシュチェック
    ├─ HIT → 即表示
    └─ MISS → Firebase Firestore fetch（chunk分割）
                └─ 全chunk完了 → localStorageに保存
```

**Overpassは絶対にuser-facingで使わない。**
理由: HTTP 200でXML error bodyを返す（`text.startsWith('<')`チェック必須）。
ingest時のみAdmin SDKで使用。

---

## データ構造（Firestore）

```
cities/{cityKey}/chunks/{0-14}
```

**トイレオブジェクト:**
```js
{
  id, name, lat, lng,
  cat,           // 'Public'|'Convenience'|'Station'|'Partner'
  free,          // boolean
  isPartner,     // boolean
  isUnconfirmed, // boolean
  hours,         // string or null
  tier,          // 1-4
  source,        // 'google'|'osm'
}
```

---

## Tier システム

| Tier | 色 | 条件 | JP表示 | EN表示 |
|---|---|---|---|---|
| T1 Green | 🟢 | 公衆トイレ, 日本の駅, Whole Foods/Target/TJ | 確実 | Reliable |
| T2 Orange | 🟠 | 日本のコンビニ | たぶん使える | Likely Available |
| T3 Yellow | 🟡 | US 7-Eleven等, ホテル | 要確認 | Ask First |
| T4 Red | 🔴 | オフィスビル, 単体"Bathroom"エントリ | 声がけ必要 | Permission Needed |
| Unconfirmed | ⚪ | 未確認 | 未確認 | Unconfirmed |
| Partner | 💜 | IBD提携 | IBD提携 | IBD Partner |

**重要:** `isPartner` は `isPublicPlace()` チェックより先に確認すること。

---

## 都市リスト（15都市）

| City key | ラベル | center | zoom |
|---|---|---|---|
| manhattan | Manhattan, NY | 40.754,-74.003 | 13 |
| tokyo | Tokyo 東京 | 35.690,139.760 | 12 |
| osaka | Osaka 大阪 | 34.693,135.502 | 13 |
| kobe | Kobe 神戸 | 34.690,135.195 | 13 |
| london | London | 51.505,-0.090 | 13 |
| sydney | Sydney | -33.868,151.209 | 13 |
| melbourne | Melbourne | -37.813,144.963 | 13 |
| brisbane | Brisbane | -27.467,153.028 | 13 |
| fukuoka | Fukuoka 福岡 | 33.590,130.402 | 13 |
| sapporo | Sapporo 札幌 | 43.062,141.354 | 13 |
| nagoya | Nagoya 名古屋 | 35.181,136.906 | 13 |
| kyoto | Kyoto 京都 | 35.012,135.768 | 13 |
| hiroshima | Hiroshima 広島 | 34.396,132.459 | 13 |
| naha | Naha 那覇 | 26.335,127.680 | 13 |

**総ロケーション数: ~40,000**

---

## データソース戦略

### ⚠️ Google Maps Platform 料金変更（2025年3月1日施行）
**$200月額クレジット廃止。SKU別無料枠に変更。**

| カテゴリ | 月間無料枠 | 主なSKU |
|---|---|---|
| Essentials | 10,000リクエスト | Nearby Search Basic, Place Details Essentials |
| Pro | 5,000リクエスト | Nearby Search Pro, Place Details Pro |

### データソース別用途
| ソース | 用途 | コスト |
|---|---|---|
| OSM `amenity=toilets` | 公衆トイレ単体（T1） | 無料 |
| Google Places API | 商業施設（T2〜T3） | SKU別課金 |
| iknowibd.com | IBDパートナー店舗（Partner） | $0（スクレイプ） |

---

## Email / ドメイン

| アドレス | 用途 | サービス |
|---|---|---|
| hello@findoasis.app | Oasis公式 | Zoho Mail Lite ($15/年) |
| hello@ippei.bet | INK / 個人用 | 同Zohoアカウント エイリアス |

---

## SNS

| プラットフォーム | アカウント | 状態 |
|---|---|---|
| X / Twitter | @oasis_app_web | 作成済み、0投稿 |
| Reddit | 未作成 | hello@ippei.betで作成予定 |

---

## 重要ルール / 既知ハマりポイント

- `.mk` クラスに `max-width:100%` を当てるとマーカーが崩れる
- Leafletはinline embed（CDN非依存）
- `tr()` 関数（`t()`からリネーム、Leaflet内部変数衝突回避）
- `map.getBounds()` は `setView()` 直後は古い値を返すことがある → `requestAnimationFrame` で待つ
- `map.invalidateSize()` はHUDやsidebar変更後に必須
- Overpass APIはこのサーバーから403ブロック → ブラウザ経由のみ
- Apostropheを含む名前（McDonald's等）はJS stringで要注意
- `isPublicPlace()` は `isPartner` チェックを先に行うこと
- `source` フィールド（'google'|'osm'）→ ingestスクリプトで必ずセット

---

## デプロイルール（厳守）

- Deploy回数制限なし（技術制約なし、Netlify無料枠内で実質無制限）
- 全pushは diff 確認後のみ実行
- ユーザー影響ある修正は最優先で即push OK（待たせない）
- 同じバグで3回以上push繰り返したら立ち止まる（根本原因未解決の証拠）
- 大規模リファクタや新機能追加はロールバック容易性のため小さく分割
- deployは俺（オーナー）の明示指示後のみ
- エラーが出ても即deployしない。原因特定してから1発で直す

---

## Places APIインジェスト承認制

新都市追加・再インジェスト前に必ずコスト試算をオーナーに提示し、明示的なYesをもらうまで実行禁止。

---

## セッション開始時の確認事項

1. 本SSOTをアップロード
2. 「SSOT読んで。Oasis appのCTO頼む。」で引き継ぎ

---

## Cross-project mistakes (Hum-derived)
Hum project (humfamily.com) で 2026-04-26〜04-28 に確立された mistake log のうち、
project 横断適用可能な5項目を Oasis に移植。
Hum philosophy framework と整合、Oasis core-philosophy 6原則 + audit-checklist 5軸にマッピング。

### mistake 11: 推測実装禁止
**症状**: 既存 helper / utility / logic の存在を確認せず、推測で新規実装してしまう。結果、format 重複 / bypass logic 発生 / philosophy 軸 (upstream format 統一) violation。
**rule**:
- 新規実装着手前、必ず src grep / git log で既存 logic 存在確認
- 「既存 helper の有無」を Plan Mode 必須項目に組み込む
- 推測で format 提案禁止、code 引用で根拠提示
- 事実確認 + 既存状態 + 技術 risk の3軸で audit
**Oasis 適用**: ingest scripts 27本の lib/ refactor 時、既存 tier 判定 logic / schema 定義の存在を grep で完全 enumeration、推測で新規 logic 書かない。

### mistake 12: 視覚仕様の配置形式確認義務
**症状**: 配置形式 (container 独立 / overlay / inline / sidebar) が複数解釈可能な視覚要求時、Plan で参考画像 / 配置 sketch を確認せず実装着手 → 完成後 Yusuke 真意と乖離発覚 → rework。
**rule**:
- 配置形式が複数解釈可能な視覚仕様要求時、Plan Mode で参考画像 / 配置 sketch を Yusuke に確認してから着手
- CTO 解釈で先に進めず、視覚 rapid prototype を先出し
- variation table に「配置形式 (container/overlay/inline/sidebar)」軸を必ず含める
**Oasis 適用**: 地図 UI / pin 配置 / filter UI 等の視覚要求時、city × zoom × filter 状態の variation table + 配置 sketch を Plan Mode で Yusuke 確認後着手。tier色 / cluster icon / detail sheet レイアウト変更も同様。

### mistake 13: 数値仕様の variation table に「実 data 範囲 simulation」必須
**症状**: 描画 logic / 数値計算系仕様の variation table が状態 2-3 種しか持たず、実際の input 値範囲での描画結果 simulation が抜ける → 完成後に scale dilution / 表示不能発覚。
**rule**:
- 描画 logic / 数値計算系仕様の variation table に「実際の input 値範囲で描画結果が想定通りか」simulation step を必須化
- input 値の min / max / median / outlier 4点で simulation 実施、各点の出力値を variation table に記載
- scale dilution / clipping / overflow 等の数値 risk を Plan Mode で先出し
**Oasis 適用**: tier 計算 logic / region 判定 logic / Firestore query filter の数値 spec 時、実際の data 範囲 (41,580件 + tier 値分布 + region 値分布) で simulation 実施。
具体例: cluster cellSize 修正時、zoom 11/12/13/14 × 神戸/東京/Manhattan の組み合わせ全部 simulation してから push。zoom 12 で cellSize=0.2度=22km 想定漏れが今日のクラスタ3個問題の原因。

### mistake 14: 実機 test 依頼 prompt 必須項目 4点 checklist
**症状**: Yusuke 向け実機 test 依頼 prompt に確認 URL / 環境 / cache 状態 明記漏れ → 古い commit 状態 / 別環境 / cache 残留状態で確認 → 「直ってない」誤判定 → panic / rework。
**rule**: Yusuke 向け実機 test 依頼 prompt に以下4点必須:
1. **確認 URL** (本番 / preview / dev 明示、URL 完全形)
2. **commit/push/deploy 状態** (commit hash + Netlify deploy 完了確認手順)
3. **cache clear 手順** (mobile Safari / mobile Chrome / desktop 別、具体 step 列挙)
4. **確認項目 list** (期待動作明示、success criteria を測定可能形で記載)
**Oasis 適用**: city × zoom × filter 状態の実機 test 時、上記4点 checklist を prompt 末尾必須化。
- iOS Safari: 設定 → Safari → 履歴とWebサイトデータ消去
- iOS Chrome: 設定 → プライバシー → 閲覧履歴データを削除
- Desktop: Cmd+Shift+R (Mac) / Ctrl+Shift+R (Win)
- Netlify deploy 完了確認: https://app.netlify.com → Site → Deploys で commit hash 表示確認

### mistake 15: 実機 test URL 提示時、現行 URL pattern を src grep で fact 確認
**症状**: 実機 test URL を Yusuke に提示時、現行 routing を src grep で確認せず、過去の URL pattern / memory ベースで提示 → 古形式 URL 提示で Yusuke が 404 遭遇 → panic 誘発。
**rule**:
- 実機 test URL を Yusuke に提示する直前、必ず現行 routing logic を src grep で fact 確認
- memory ベースの URL pattern 提示禁止、src 引用で根拠提示
**Oasis 適用**: Oasis は単一 HTML + Firestore read 構造、URL routing 仕様が Hum と異なる。
- 実機 test URL は基本 https://findoasis.app のみ（routing なし）
- activeCity は内部状態で URL に反映されない（URL parameter 未実装）
- 将来 URL parameter 追加時 (?city=kobe 等) は src grep で fact 確認必須

---

## philosophy framework との対応
| Hum mistake | Oasis core-philosophy 対応 | Oasis audit-checklist 軸 |
|---|---|---|
| 11. 推測実装禁止 | 原則5 (AI-only verification) | 軸1 (状態変数 audit) |
| 12. 視覚仕様の配置形式 | 原則2 (ピンが見えなければ意味なし) | 軸2 (描画 audit) |
| 13. 実 data 範囲 simulation | 原則4 (ロード時間は UX) | 軸4 (Variation table) |
| 14. 実機 test 4点 checklist | 原則6 (Visibility 依存禁止) | 軸5 (SSOT 更新) |
| 15. URL pattern fact 確認 | 原則5 (AI-only verification) | 軸1 (状態変数 audit) |
