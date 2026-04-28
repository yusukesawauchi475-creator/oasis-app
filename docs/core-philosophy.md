# Oasis Core Philosophy

## 原則1: 調査なき修正は存在しない
修正前に必ず root cause を特定する。「たぶんこれ」で push しない。

## 原則2: diff は BOSS が読む
Claude Code の diff 出力は BOSS が直接読んで承認する。CTO は転送するだけ。

## 原則3: push 前に副作用を列挙する
修正が他の経路に影響しないか、関連コードを全部確認してから push する。

## 原則4: 同じバグで3回 push したら止まる
根本原因が解決されていない証拠。アプローチを根本から変える。

## 原則5: 状態変数を変える修正は対称性を確認する
activeCity, allToilets, searchPin, userLat/Lng, currentLoadKey のいずれかを変える修正は、関連状態を全部リスト化してから書く。

## 原則6: 「完了」宣言は実機確認後のみ
コードが通っても「完全修正」と言わない。BOSS の実機確認が取れるまで完了扱いしない。
