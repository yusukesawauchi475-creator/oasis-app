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

## Current state（2026-04-08 v4）

### データ
- 全14都市・約40,000件（Manhattan/London/Tokyo/Osaka/Kobe/Sydney/Melbourne/Brisbane/福岡/札幌/名古屋/京都/広島/那覇）
- Manhattan bbox拡張済み（Brooklyn/Queens/Jersey City含む、lng<-74.0で1,607件確認済）
- Firestoreチャンク構造: cities/{cityKey}/chunks/{0-14}
- isPartner:true は0件（IBD ingest未実行）

### UI/UX実装済み
- TIER_CONFIG（brands/types/colors/display）
- Bottom tab 2枚（Near Me / Search）
- 段階展開（T1+T2P+PARTNER→T2M→T3→T4）
- 詳細シート v2（タイミー風）：施設名+Tierバッジ+顔アイコン、星評価3段階、🕐💴情報行、3D shadowボタン、🚪🙅🔒投票
- 詳細シートボタン: JP「📍ルート案内」「🚩報告」/ EN「📍Directions」「🚩Report」
- 星評価: デフォルトgrayscale(1) opacity(0.25)、タップで光る
- JP/ENトグル（localStorage保存、地図上部中央）
- 赤rippleピン（現在地 me-dot divIcon）
- 検索結果ピン: L.circleMarker（SVG、CSS依存なし）
- ロゴ差し替え（oasis-logo.jpg）
- ローディングblur reveal アニメーション
- hideLoading display:none修正
- フィルターバー: 「すべて / 🟢絶対入れる(tier===1) / 🔵ほぼ入れる(tier1or2)」3つのみ
- 凡例：色ドット5個のみ→タップで展開（toggle式）
- Tier表示：確実/たぶん使える/要確認/声がけ必要/要確認/IBD提携
- IBDフィルター削除済み

### 検索（2026-04-08更新）
- Google Places Autocomplete (New) `places.googleapis.com/v1/places:autocomplete`
- リクエスト: `languageCode:'ja'`, `regionCode:'JP'`
- placeId → Place Details で座標取得
- detectCity null時は最近傍都市にfallback（nearestCity関数）
- 徒歩時間: searchPin優先、なければGPS（getOriginLatLng）
- **Nominatim廃止済み**

### パフォーマンス改善（2026-04-08）
- `loadCity()`: chunk 0-14を `Promise.all` 並列化（直列3-7秒→1秒以下）
- `isLoadingCity` フラグで二重実行ガード
- `init()`: geolocation callback で別都市検出時は末尾の loadCity をスキップ
- `refreshZoom()`: `isRefreshing` フラグで `zoomend`/`moveend` 無限ループ防止
- `refreshZoom()`: `refreshQueued` フラグでフィルター連打対応（ブロック中の呼び出しを後追い処理）
- zoom>=14時のbounds取得を `requestAnimationFrame` で遅延（flyTo直後のstale bounds対策）
- viewport内のみマーカー描画（zoom>=14）
- localStorageキャッシュ: `oasis_v4_*` → `oasis_v5_*` にバスト
- キャッシュ読み込み時 `Array.isArray(d) && d.length > 0` ガード
- emptyState発火条件: `toilets.length===0 && opts.fetchFailed`（chunk全失敗時のみ）

### 残課題
1. ~~Search後にloadCity()が呼ばれない~~ → 修正済み（fe6d753）
2. ~~loading forever（loadCity二重実行）~~ → 修正済み
3. ~~検索→トイレ0件バグ~~ → 修正済み（nearestCity fallback）
4. ~~refreshZoom無限ループ~~ → 修正済み（isRefreshing flag）
5. ~~Weehawkenで「データなし」表示~~ → 修正済み（cache guard, fetchFailed only, rAF bounds, v5バスト）
6. ~~フィルター押しても変わらない~~ → 修正済み（refreshQueued + 新フィルター3種）
7. ~~検索→ピン出ない~~ → 修正済み（circleMarker化）
8. JP/ENが実機で正しく動くか未確認
9. findoasis.appの実機総合確認が未実施
10. IBDパートナーingest未実行（isPartner:true 0件）

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
