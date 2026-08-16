---
id: KNO-GH-001
type: playbook
lifecycle: observed
confidence: 0.94
derivation: extracted
validation: documented
source_repositories:
  - ganase/pdf2csv
---

# API keyはOS資格情報ストアまたは管理環境変数へ保存する

## 要点

利用者向け端末ではOSの資格情報ストアへAPI keyを保存する。組織が固定管理する場合は環境変数を使い、画面から変更できないようにする。

## 何から分かったか

`ganase/pdf2csv`のREADMEでは、API keyを`.env`ではなくOSのローカル資格情報ストアへ保存すると説明している。組織管理では環境変数を優先し、旧`.env`があれば資格情報ストアへ移行後に削除する方針も記載されている。

## 判断に使えること

- デスクトップ製品の資格情報保存を共通化する候補になる
- 個人試用と組織管理で保存方法を分けられる
- 設定ファイルや共有フォルダへの秘密情報混入を減らせる

## 注意

今回はREADMEの記載確認であり、資格情報ストアへの保存実装と移行処理は未確認である。

## 出典

- [ganase/pdf2csv README](https://github.com/ganase/pdf2csv/blob/541d88bbfdfe0b76d1dac7c79f7bb499cbcfb4a9/README.md) — documentation

## 関連

- [セットアップ時に.envへAPI keyを設定する](KNO-GH-002.md)
- [外部LLM送信前にPII・秘密情報を検査する](KNO-GH-003.md)
