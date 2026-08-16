---
id: KNO-GH-003
type: playbook
lifecycle: candidate-standard
confidence: 0.96
derivation: extracted-and-linked
validation: implemented
source_repositories:
  - ganase/pdf2csv
  - ganase/aiagent_workspace
---

# 外部LLM送信前にPII・秘密情報を検査する

## 要点

外部モデルへ送る直前に個人情報や秘密情報を検査し、該当時は送信を止めて人へ戻す。

## 何から分かったか

`ganase/pdf2csv`では、READMEの説明に加えて次の実装を確認できた。

- `pii_detector.py`がメールアドレス、電話番号、マイナンバー、クレジットカード番号、郵便番号を検出する
- `pdf_process_svc.py`が検出結果を確認し、該当時はLLM呼び出し前に`pii_detected`として終了する

`ganase/aiagent_workspace`でも、Secret読取や認証情報の外部送信をブロック対象とする方針がREADMEに記載されている。

## 標準化候補になった理由

- 独立した2つのrepositoryで、外部送信前の安全確認が扱われている
- 一方では検出と送信中断の実装まで確認できる
- KUMONOS自身も、GitHubやログをLLMへ送る前に同じ境界が必要になる

## 次の行動

検出対象、誤検知時の扱い、画像やbinaryで検査できない場合の処理を整理し、共通ライブラリ化できるか検討する。

## 注意

正規表現だけで完全な検出はできない。画像PDFではテキスト抽出できず、README上も検査をスキップする制約が記載されている。

## 出典

- [ganase/pdf2csv README](https://github.com/ganase/pdf2csv/blob/541d88bbfdfe0b76d1dac7c79f7bb499cbcfb4a9/README.md) — documentation
- [ganase/pdf2csv pii_detector.py](https://github.com/ganase/pdf2csv/blob/541d88bbfdfe0b76d1dac7c79f7bb499cbcfb4a9/app/services/pii_detector.py) — implementation
- [ganase/pdf2csv pdf_process_svc.py](https://github.com/ganase/pdf2csv/blob/541d88bbfdfe0b76d1dac7c79f7bb499cbcfb4a9/app/services/pdf_process_svc.py) — implementation
- [ganase/aiagent_workspace README](https://github.com/ganase/aiagent_workspace/blob/fdd618cc9c2b1fb837cdbb4b337eddc3bf15fe3c/README.md) — documentation

## 関連

- [API keyはOS資格情報ストアまたは管理環境変数へ保存する](KNO-GH-001.md)
- [元データを変更せず派生物を別に保存する](KNO-GH-004.md)
