---
id: KNO-GH-006
type: playbook
lifecycle: observed
confidence: 0.90
derivation: extracted
validation: partially-implemented
source_repositories:
  - knockknock-at/lifeloop
---

# OS権限は目的を説明してから段階的に要求する

## 要点

起動直後に権限ダイアログを出さず、何のために必要かを画面で説明する。その後、前景利用から常時利用へ段階的に進める。

## 何から分かったか

`knockknock-at/lifeloop`のREADMEでは、Home画面の権限cardで位置情報と通知の目的を説明してから、`When In Use`、`Always`の順に要求する設計が説明されている。

`LocationService.swift`には二つの権限要求methodと、許可状態に応じたRegion Monitoring処理が実装されている。

## 判断に使えること

カメラ、ファイルアクセス、外部送信などを使う別製品でも、同じ説明順序を共通UXとして使える可能性がある。

## 注意

説明card自体の実装は今回確認していないため、`partially-implemented`としている。iOS以外では権限modelが異なる。

## 出典

- [knockknock-at/lifeloop README](https://github.com/knockknock-at/lifeloop/blob/ef218a09afecace9f8f91f5281e97d9551f0684f/README.md) — documentation
- [knockknock-at/lifeloop LocationService.swift](https://github.com/knockknock-at/lifeloop/blob/ef218a09afecace9f8f91f5281e97d9551f0684f/Services/LocationService.swift) — implementation

## 関連

- [非技術者向け導入をダブルクリック中心にする](KNO-GH-005.md)
- [外部LLM送信前にPII・秘密情報を検査する](KNO-GH-003.md)
