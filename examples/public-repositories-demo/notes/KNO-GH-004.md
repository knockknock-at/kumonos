---
id: KNO-GH-004
type: playbook
lifecycle: candidate-standard
confidence: 0.94
derivation: extracted-and-linked
validation: implemented
source_repositories:
  - ganase/pdf2csv
  - ganase/stock_market_index
  - knockknock-at/kumonos
---

# 元データを変更せず派生物を別に保存する

## 要点

入力を正本として保持し、加工結果は再生成可能な別フォルダまたは別ファイルへ保存する。

## 何から分かったか

- `ganase/pdf2csv`は元PDFを変更せず、rename済みcopyとCSVを別フォルダへ出す
- `ganase/stock_market_index`は元系列、構成銘柄、派生panel、Tableau向けexportを分ける
- `knockknock-at/kumonos`は入力ファイルを変更せず、生成物を再構築可能にする方針を持つ

`stock_market_index`の実装では、一時ファイルを作ってから変更時だけ出力へ反映し、派生行へ`source_file`を残している。

## 標準化候補になった理由

3つの異なる製品で同じ原則が確認できるため、データ処理製品の共通チェックリストにできる可能性が高い。

## 次の行動

入力変更禁止、派生物の保存場所、再生成方法、出典列、削除・保持期間を共通設計項目にする。

## 出典

- [ganase/pdf2csv README](https://github.com/ganase/pdf2csv/blob/541d88bbfdfe0b76d1dac7c79f7bb499cbcfb4a9/README.md) — documentation
- [ganase/stock_market_index README](https://github.com/ganase/stock_market_index/blob/c1d49b6612308664070e15045b05049fe2cbbf29/README.md) — documentation
- [ganase/stock_market_index build script](https://github.com/ganase/stock_market_index/blob/c1d49b6612308664070e15045b05049fe2cbbf29/scripts/build_and_publish_tableau_feed.py) — implementation
- [knockknock-at/kumonos README](https://github.com/knockknock-at/kumonos/blob/fe58ea655d1bc3d664a3db2f7e7ce0878869aa7b/README.md) — documentation

## 関連

- [派生データにsource_fileを残す](KNO-GH-009.md)
- [外部LLM送信前にPII・秘密情報を検査する](KNO-GH-003.md)
