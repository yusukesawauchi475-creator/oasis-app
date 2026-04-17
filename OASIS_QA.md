# Oasis Routine QA Prompt
毎晩Claude Codeで実行するQAチェック。

## 実行方法
claude --dangerously-skip-permissions でClaude Code起動後、このファイルの内容を貼る。

## QAプロンプト

以下を全部チェックしてGitHub issue形式で報告。severity: Critical/High/Medium/Low。

### 1. Tier判定ロジック整合性
index.htmlのtierKey()を読んで：
- T1_US brandsリストに抜けがないか
- T2_PLUS brandsに誤りがないか
- majorTerminalsリストが最新か
- JP_CITIESリストが都市リストと一致してるか

### 2. L10N完全性チェック
index.htmlのL10Nオブジェクト（JP/EN）を読んで：
- JPにキーがあってENにないもの
- ENにキーがあってJPにないもの
- ハードコードされた日本語/英語文字列がHTML内にないか
- tr()関数で参照されてるキーがL10Nに存在するか

### 3. Firestore構造チェック
firestore.rulesを読んで：
- allow write: if true になってる箇所がないか
- reviewsコレクションへの書き込み制限があるか
- pending_toiletsへの書き込み制限があるか

### 4. 主要関数の存在チェック
index.htmlで以下の関数が存在し、正しく接続されてるか：
- loadCity() → hideLoading()が必ず呼ばれるか
- openDetail() → reviews fetchがあるか
- goToPlaceId() → goToSearchResult()を呼ぶか
- submitAdd() → notifyNewToilet()を呼ぶか
- rateStar() → localStorage制限があるか
- quickVote() → localStorage制限があるか

### 5. デプロイ前チェック
- alert()やconsole.log('[DEBUG]')等のデバッグコードが残ってないか
- TODO/FIXMEコメントが新たに追加されてないか
- git statusでコミット漏れがないか

### 6. SSOTと実装の乖離
OASIS_SSOT.mdのCurrent stateと実際のindex.htmlを比較して：
- SSOTに書いてある機能が実装されてるか
- 実装されてるがSSOTに記載がない機能がないか

## 報告フォーマット
各問題を以下で報告：
**[severity] タイトル**
- 場所: ファイル名:行番号
- 内容: 何が問題か
- 修正案: どう直すか

問題なければ「✅ Clean - YYYY-MM-DD」と報告。

### 7. ユーザーデータ整合性
Firestoreを確認：
- reviews コレクションの全件でtoiletId/cityKey/tsフィールドが存在するか
- reviewSummariesのtotalがreviewsの実件数と一致してるか
- pending_toiletsでstatus:'pending'のまま7日以上経過してるものがないか
- rated_${toiletId}とvoted_${toiletId}のlocalStorage制限が両方のコレクションで機能してるか

### 8. ボタン・インタラクション完全チェック
index.htmlで以下を確認：
- フィルターボタン（すべて/今すぐ入れる）のonclick/data-f属性が正しく接続されてるか
- rateStar()の星ボタンにonclick属性があるか
- quickVote()の3ボタン（入れた/断られた/閉鎖中）にonclick属性があるか
- ルート案内ボタンがGoogle Maps URLを開くか
- 報告ボタンがreportsコレクションに書き込むか
- +ボタンがsubmitAdd()を呼ぶか
- JP/ENトグルが5回タップでadminモードになるロジックがあるか

### 9. JP/EN混在チェック
index.htmlを全文スキャン：
- HTML内にハードコードされた日本語文字列（ひらがな・カタカナ・漢字）がtr()外にないか
- HTML内にハードコードされた英語ラベルがtr()外にないか
- L10N JPオブジェクトに英語のみの文字列が混入してないか
- L10N ENオブジェクトに日本語文字列が混入してないか
- applyLang()が全てのtr()参照要素を更新してるか

### 10. クリティカルパス動作確認
以下のフローをコードで追跡して確認：
- GPS取得→detectCity()→loadCity()→renderCity()→renderNearby()が繋がってるか
- 検索入力→autocomplete→goToPlaceId()→goToSearchResult()→loadCity()が繋がってるか
- マーカーtap→openDetail()→reviews fetch→UI更新が繋がってるか
- +ボタン→フォーム→submitAdd()→Firestore保存→notifyNewToilet()が繋がってるか

QA完了後、~/Oasis/OASIS_QA_REPORT_$(date +%Y%m%d).md に結果を保存。
