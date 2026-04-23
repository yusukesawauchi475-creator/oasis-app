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
| Firebase API Key | AIzaSyDXQabNFmpISVQ4O_yCP6dTyx-UC_uGQLw |
| Google Places API Key | AIzaSyDVuhME-g_3QakgS4cmtWlYR01uns2kG1A |

---

## Current state（2026-04-22 v4.1）

### データ
- 全14都市・約40,000件（Manhattan/London/Tokyo/Osaka/Kobe/Sydney/Melbourne/Brisbane/福岡/札幌/名古屋/京都/広島/那覇）
- Manhattan bbox拡張済み（Brooklyn/Queens/Jersey City含む、lng<-74.0で1,607件確認済）
- Firestoreチャンク構造: cities/{cityKey}/chunks/{0-14}
- isPartner:true は0件（IBD ingest未実行）
- pending_toilets: City Point Brooklyn → status:approved（chunk 11に追加済み）
- JP都市名日本語化: 7,600件変換済み（英語名73.4%→33.6%に改善）、残り6,434件は店名等でそのまま

### UI/UX実装済み
- TIER_CONFIG（brands/types/colors/display）
- Bottom tab 2枚（Near Me / Search）
- 段階展開（T1+T2P+PARTNER→T2M→T3→T4）
- フィルター：「すべて」「🩵今すぐ入れる」2つのみ（tier===1フィルタ）
- Tier色：T1=水色(#ADE8F4)、T2_PLUS=緑(#4CAF50)、T2_MINUS=オレンジ(#E67E22)、T3=黄、T4=赤（非表示）
- 詳細シート v2：顔アイコン(😶😟🙂😄)、星評価3段階(grayscaleデフォルト)、投票件数表示(🚪🙅🔒)、3Dボタン
- 詳細シートボタン: JP「📍ルート案内」「🚩報告」/ EN「📍Directions」「🚩Report」
- one-vote制限: localStorage `rated_${toiletId}` / `voted_${toiletId}` で重複防止
- 星評価: 再オープン時に自分の評価値で星表示（localStorageから復元）
- reviewSummaries: rateStar→ratingTotal/ratingCount、quickVote→access/refused/closed を increment
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
- レビュー通知メール: rateStar/quickVote/submitReview → notifyNewReview() → EmailJS
- L10N: 70キーJP/EN完全一致（未使用15キー削除済み）

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
- リクエスト: `languageCode:'ja'`, `regionCode:'JP'`, `maxResultCount:5`
- locationBias: activeCity中心50km circle
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
- `.github/workflows/nightly-qa.yml`: 毎日JST 2:00にClaude APIでQA実行
- `OASIS_QA.md`: 10項目チェックリスト
- Critical/High → GitHub Issue自動作成
- 要: ANTHROPIC_API_KEY secret設定

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
- キャッシュ読み込み時 `Array.isArray(d) && d.length > 0` ガード
- emptyState発火条件: `toilets.length===0 && opts.fetchFailed`（chunk全失敗時のみ）
- 各chunkに10秒タイムアウト（withTimeout）

### Firestoreルール（簡易版、2026-04-22適用済み）
- reviews: read+create+delete（admin.html用）、update不可
- pending_toilets: read+create+update（承認用）、delete不可
- cities: read+write（承認chunk追加用）
- reports: read+create
- stats: read+create+update
- TODO: マーケ前にFirebase Auth導入してcustom claim admin判定に移行

### 残課題
1. I know IBD Partner ingest未実行（isPartner:true 0件）
2. 投票でtier自動変更未実装
3. Firebase Auth導入（マーケ開始前必須）
4. 英語名残り6,434件の処理（店名等、優先度低）
5. Manhattan bbox拡張（Weehawken/Hoboken追加ingest検討）
6. マーケ開始（X @oasis_app_web 初投稿）

### 明日のタスク（優先順）
1. admin dashboard可視化強化（訪問者グラフ日別/週別、レビューマップ可視化、都市別マップリンク）
2. 検索ワード拡張（10倍化）- Google Places Autocomplete追加検討
3. Manhattan bbox拡張（Weehawken/Hoboken/Jersey City）
4. Firebase Auth導入（マーケ開始前必須）
5. レビュー設問の再設計（3問タップ式に変更検討）
   - 現状: ⭐5評価 + 入れた/断られた/閉鎖中 + 詳細(access/priv/paper) + コメント
   - 問題: IBD患者はトイレ出た直後にサッと答えたい（体調悪い状態）
   - 提案: 3問タップ式（自由記述なし、1タップ×3で完了）
     Q1. 入れましたか？ → 🚪入れた / 🙅断られた / 🔒閉鎖中
     Q2. 清潔さ → ✨きれい / 🆗普通 / 🚫汚い
     Q3. 紙・広さ → 📄紙あり+広い / 📄紙のみ / 🚫紙なしor狭い
   - 追加調査要: 「紙」「広さ」「音漏れ」「待ち時間」のうちIBDコミュニティで最重要な2項目を絞る（X/Redditで軽く調査）

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

## 都市リスト（14都市）

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

- 1セッション最大5 deploys
- デプロイ前にコード確認必須
- 同じエラーで3回失敗したらアプローチ変更、デプロイ停止
- エラーが出ても即デプロイしない。原因特定してから1発で直す

---

## Places APIインジェスト承認制

新都市追加・再インジェスト前に必ずコスト試算をオーナーに提示し、明示的なYesをもらうまで実行禁止。

---

## セッション開始時の確認事項

1. 本SSOTをアップロード
2. 「SSOT読んで。Oasis appのCTO頼む。」で引き継ぎ
