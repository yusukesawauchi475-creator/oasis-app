# Oasis — ハイブリッドデータアーキテクチャ設計

## 現状の問題分析

### bbox依存の限界
- 各都市のbboxを手動で定義。カバー外のエリアはデータなし
- bbox拡張にはre-ingest + コスト発生
- 都市間の隙間エリア（郊外、地方都市）は永久にカバー不可

### 月次更新の手間
- 新規開店/閉店の反映にラグ
- re-ingestは全都市でコスト大（14都市×$15-40 = $210-560）
- 営業時間の変更が反映されない

### スケール限界
- 15都市で41,580件 → Firestore読み取りコスト増
- 都市追加のたびにingestスクリプト実行 + bbox定義 + CITIES更新
- 100都市展開は現実的に困難

---

## ハイブリッド方式の設計

### 概要
```
ユーザーアクセス
    ↓
[Phase 1] Firestore Static Data（即時表示）
    └── 公衆トイレ / 公園トイレのみ（T1, 確実に使える場所）
    └── 全都市プリロード、localStorageキャッシュ24h
    ↓
[Phase 2] Google Places Nearby API（リアルタイム）
    └── コンビニ / カフェ / スーパー / 駅（T2+以下）
    └── ユーザーの現在地中心 500m-1km
    └── クライアント側キャッシュ TTL 5分
```

### Static Layer（Firestore）
- **対象:** public_bathroom, park のみ
- **更新頻度:** 月1回（OSM bulk download、$0）
- **データ量:** 全都市で推定 8,000-10,000件（現在の~20%）
- **メリット:** 完全無料、即時表示、オフライン対応可能

### Realtime Layer（Google Places API）
- **対象:** convenience_store, cafe, supermarket, train_station, restaurant
- **API:** Nearby Search (New) — クライアント側から直接呼び出し
- **呼び出しタイミング:**
  - 初回位置取得時
  - 地図移動完了時（debounce 1秒）
  - 都市切替時
- **レスポンスキャッシュ:** sessionStorage、キー=`nearby_{lat}_{lng}_{types}`、TTL=5分
- **FieldMask:** `places.id,places.displayName,places.location,places.types`（Essentials、$0.0085/件）

### キャッシュ戦略
```
Client Side:
├── localStorage: Static Layer（public_bathroom/park）— 24h TTL
├── sessionStorage: Realtime Layer（convenience_store等）— 5min TTL
└── allToilets: メモリ内で Static + Realtime をマージ

Cache Key: nearby_{Math.round(lat*100)}_{Math.round(lng*100)}_{type_hash}
```

---

## コスト試算

### 現状（Full Static）
| 項目 | コスト |
|---|---|
| Firestore読み取り | ~$0.50/月（50,000 reads無料枠内） |
| 初回ingest | $15-40/都市 |
| 月次re-ingest | $210-560/全都市 |
| **月額合計** | **$0.50 + re-ingest時のみ** |

### ハイブリッド方式
| 項目 | コスト |
|---|---|
| Firestore読み取り | ~$0.20/月（Static層のみ、データ量1/5） |
| Places Nearby (Essentials) | $0.0085/件 × 月10,000件 = $85/月 |
| Places Nearby (Pro) | $0.017/件 × 月5,000件 = $85/月 |
| **月額合計** | **$85-170/月** |

### 無料枠活用プラン
- Essentials SKU: 月10,000件無料
- 1ユーザーあたり平均3-5回のNearby呼び出し
- 無料枠で2,000-3,000 DAU対応可能
- DAU超過時のみ課金発生

---

## 段階的移行プラン

### Phase 0: 現状維持（〜マーケ開始）
- Firestore Full Static
- 都市追加は手動ingest
- コスト: ほぼ$0

### Phase 1: Static + Nearby（マーケ開始後、DAU 100-1,000）
- Firestoreに公衆トイレ/公園のみ保持
- コンビニ/カフェはNearby APIでリアルタイム取得
- 既存データからpublic_bathroom以外を削除
- 月額: $0（無料枠内）

### Phase 2: Nearby Only（DAU 1,000+）
- Firestoreは完全廃止（またはレビュー/ユーザーデータのみ）
- 全データをNearby APIでリアルタイム取得
- CDN/Cloudflare Workersでキャッシュ
- 月額: $85-170

### Phase 3: OSM + Nearby（DAU 10,000+）
- OSM公衆トイレデータ（無料）をベースに
- 商業施設はNearby API
- 独自POIデータベース構築
- 月額: $170-500

---

## 懸念事項と対策

### 1. API Key露出
- **懸念:** クライアント側でPlaces APIを直接呼ぶとAPI Keyがフロントに露出
- **対策:** API Keyのリファラー制限（findoasis.app/*のみ）+ 月間クォータ上限設定

### 2. レイテンシ
- **懸念:** Nearby APIの応答時間200-500ms。Static層（キャッシュ）は0ms
- **対策:** Static層を先に表示 → Nearby結果を後からマージ（progressive）

### 3. 一貫性
- **懸念:** Static層とRealtime層でデータ重複
- **対策:** place_idで重複除外。Static層のpublic_bathroomはRealtime層では取得しない

### 4. オフライン
- **懸念:** Nearby APIはオフラインで使えない
- **対策:** Static層（localStorage）はオフラインでも表示。Nearby層は「データ取得中...」表示

### 5. 地方都市
- **懸念:** Nearby APIは都市部以外で結果が少ない
- **対策:** OSM公衆トイレデータ（無料）で地方カバー。Nearby APIは都市部の商業施設のみ

---

## 判断サマリー（2026-04-23）
- Phase 0継続でマーケ開始
- Phase 1移行はDAU 500超えてから検討
- 優先対応：
  1. bbox拡張スクリプトの簡易化
  2. GitHub Actions月次cron自動化
