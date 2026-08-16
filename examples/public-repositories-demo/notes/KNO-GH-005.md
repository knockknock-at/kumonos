---
id: KNO-GH-005
type: playbook
lifecycle: repeated
confidence: 0.92
derivation: inferred-from-repetition
validation: documented
source_repositories:
  - ganase/aiagent_workspace
  - ganase/pdf2csv
  - knockknock-at/cut-in-meter
---

# 非技術者向け導入をダブルクリック中心にする

## 要点

ZIPを展開し、`SETUP.bat`や`setup_windows.bat`をダブルクリックするところから導入を始める。Python確認、仮想環境作成、依存導入などをscriptへ閉じ込める。

## 何から分かったか

3つのrepositoryが、Windows利用者向けの最初の操作としてZIP展開とsetup scriptを案内している。

- `ganase/aiagent_workspace`
- `ganase/pdf2csv`
- `knockknock-at/cut-in-meter`

## 判断に使えること

各製品で似たinstallerを作り直している可能性がある。共通template化すれば、導入手順と状態確認を揃えられる。

## 注意

`aiagent_workspace`はACL保護のため管理者権限が必要だが、ほかの製品も同じとは限らない。共通化するのは部品と表示規約であり、権限要求そのものではない。

## 出典

- [ganase/aiagent_workspace README](https://github.com/ganase/aiagent_workspace/blob/fdd618cc9c2b1fb837cdbb4b337eddc3bf15fe3c/README.md)
- [ganase/pdf2csv README](https://github.com/ganase/pdf2csv/blob/541d88bbfdfe0b76d1dac7c79f7bb499cbcfb4a9/README.md)
- [knockknock-at/cut-in-meter README](https://github.com/knockknock-at/cut-in-meter/blob/8930d1407d3cecf42c841dffae50b8938c772c41/README.md)

## 関連

- [セットアップ時に.envへAPI keyを設定する](KNO-GH-002.md)
- [OS権限は目的を説明してから段階的に要求する](KNO-GH-006.md)
