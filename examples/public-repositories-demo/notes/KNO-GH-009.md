---
id: KNO-GH-009
type: playbook
lifecycle: observed
confidence: 0.98
derivation: extracted
validation: implemented
source_repositories:
  - ganase/stock_market_index
---

# 派生データにsource_fileを残す

## 要点

分析向けに複数の入力を一つのtableへ組み替えても、各行がどの元ファイルから作られたかを列として残す。

## 何から分かったか

`ganase/stock_market_index`のTableau exportは、価格と指数の両方に`source`、`source_file`、`fetched_at`を持つ。

実装では、入力pathをrepository rootからの相対pathへ変換し、生成する各行の`source_file`へ格納している。

## 判断に使えること

- 集計値に問題があるとき元fileまで戻れる
- KUMONOSのMarkdownやグラフでも同じ出典設計を使える
- Data lineageを大規模な専用基盤なしで始められる

## 注意

`source_file`だけでは入力fileの版を特定できない。GitHub入力ではcommit SHAとblob SHAも合わせて保持する。

## 出典

- [ganase/stock_market_index README](https://github.com/ganase/stock_market_index/blob/c1d49b6612308664070e15045b05049fe2cbbf29/README.md) — documentation
- [ganase/stock_market_index build script](https://github.com/ganase/stock_market_index/blob/c1d49b6612308664070e15045b05049fe2cbbf29/scripts/build_and_publish_tableau_feed.py) — implementation

## 関連

- [元データを変更せず派生物を別に保存する](KNO-GH-004.md)
