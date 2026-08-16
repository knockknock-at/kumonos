---
id: KNO-GH-007
type: decision
lifecycle: repeated
confidence: 0.88
derivation: extracted-and-linked
validation: documented
source_repositories:
  - ganase/c4
  - knockknock-at/kumonos
---

# 外部AIエンジンの差をadapterへ閉じ込める

## 要点

Codex、Claude Code、GitHubなど外部system固有の差をadapterまたはConnectorへ閉じ込め、中核の処理と画面を共通化する。

## 何から分かったか

- `ganase/c4`はCodexとClaude Codeを共通runnerから使い、engine固有部分をadapterとして差し替える設計をREADMEに記載している
- `knockknock-at/kumonos`は入力形式をConnector、出力形式をRendererへ分ける方針をREADMEに記載している

## 判断に使えること

GitHub.comとGitHub Enterpriseの違いも、中核へ分岐を増やさずGitHub Connector内部のprovider adapterで扱える。

## 注意

今回は設計文書の記載確認であり、adapter interfaceの実装比較は行っていない。

## 出典

- [ganase/c4 README](https://github.com/ganase/c4/blob/6d99e504b760bfce6f8ae5a70be6a0c02553457d/README.md)
- [knockknock-at/kumonos README](https://github.com/knockknock-at/kumonos/blob/fe58ea655d1bc3d664a3db2f7e7ce0878869aa7b/README.md)

## 関連

- [顧客別処理をpluginとCI matrixで増やす](KNO-GH-008.md)
