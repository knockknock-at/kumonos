---
id: KNO-GH-002
type: playbook
lifecycle: observed
confidence: 0.97
derivation: extracted
validation: documented
source_repositories:
  - knockknock-at/cut-in-meter
---

# セットアップ時に.envへAPI keyを設定する

## 要点

ローカルアプリの初期設定で`.env`を作り、利用者が`OPENAI_API_KEY`を記入する。

## 何から分かったか

`knockknock-at/cut-in-meter`のREADMEでは、setup scriptが`.env.example`から`.env`を作り、その後に利用者がAPI keyを設定する手順になっている。

## 判断に使えること

`ganase/pdf2csv`のOS資格情報ストア方式と異なるため、製品間で資格情報の保存方針を統一するか判断できる。

## 注意

`.env`方式が直ちに誤りという意味ではない。個人のローカル試用と、組織配布では許容できる方式が異なる。

## 出典

- [knockknock-at/cut-in-meter README](https://github.com/knockknock-at/cut-in-meter/blob/8930d1407d3cecf42c841dffae50b8938c772c41/README.md) — documentation

## 関連

- [API keyはOS資格情報ストアまたは管理環境変数へ保存する](KNO-GH-001.md)
- [非技術者向け導入をダブルクリック中心にする](KNO-GH-005.md)
