---
id: KNO-GH-008
type: playbook
lifecycle: observed
confidence: 0.95
derivation: extracted
validation: implemented
source_repositories:
  - ganase/tweepybot
---

# 顧客別処理をpluginとCI matrixで増やす

## 要点

顧客固有の処理を同じmain programへ書き足さず、plugin moduleへ分ける。CIではmatrixに顧客IDを並べ、同じworkflowを複数顧客へ展開する。

## 何から分かったか

`ganase/tweepybot`では次を確認できた。

- `plugin_loader.py`が`CLIENT`環境変数から`plugins.<client>`を動的importする
- workflowのmatrixが`cl0001`、`cl0002`、`cl0003`を同じjobで処理する
- client別のsecretをmatrixの値に応じて渡す

## 判断に使えること

KUMONOSのsource Connectorや組織別抽出ruleをplugin化するときの参考になる。

## 注意

顧客数が増えるとworkflow内の条件式とsecret名が長大化する。KUMONOSへ採用する場合は、設定dataと実装codeをさらに分離する必要がある。

## 出典

- [ganase/tweepybot README](https://github.com/ganase/tweepybot/blob/f26c57950d7d1446f1d2243b6666aebef03cc866/README.md) — documentation
- [ganase/tweepybot workflow](https://github.com/ganase/tweepybot/blob/f26c57950d7d1446f1d2243b6666aebef03cc866/.github/workflows/bot.yml) — implementation
- [ganase/tweepybot plugin_loader.py](https://github.com/ganase/tweepybot/blob/f26c57950d7d1446f1d2243b6666aebef03cc866/plugin_loader.py) — implementation

## 関連

- [外部AIエンジンの差をadapterへ閉じ込める](KNO-GH-007.md)
