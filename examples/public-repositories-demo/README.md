# 公開リポジトリ由来の出力サンプル

このフォルダは、KUMONOSがGitHubリポジトリを入力にした場合の見え方を確認するためのダミー出力です。

[knockknock-at](https://github.com/knockknock-at)と[ganase](https://github.com/ganase)の公開リポジトリから、2026-08-16時点のREADMEと代表的な実装ファイルを確認し、KUMONOSが生成しそうな形へ手作業で編成しています。

実際にKUMONOSを実行して生成した結果ではありません。また、READMEに書かれていることと、コードで確認できたことを区別しています。

## 見る順番

1. `index.html`をブラウザで開く
2. 「標準化」「食い違い」「横展開」の判断候補を選ぶ
3. グラフのNodeを選び、根拠となったrepositoryを確認する
4. `notes/`でメモ本文と固定commitへのリンクを確認する

## このサンプルから判断できる例

- 複数製品で繰り返されている安全対策を、共通部品にする価値があるか
- API keyの保存方法が製品間で異なるため、組織標準を決めるべきか
- 非技術者向けのセットアップ方法をテンプレート化できるか
- 一つのrepositoryだけにある設計を、別製品へ横展開する価値があるか

## ファイル

| ファイル | 内容 |
|---|---|
| `index.html` | 判断画面と知識グラフ |
| `sources.json` | 調査したrepository、commit、file、content SHA |
| `graph.json` | 知識Nodeと関係 |
| `decisions.json` | 標準化、食い違い解消、横展開、要検証の候補 |
| `graph.graphml` | Gephiなどへ渡すグラフ |
| `notes/` | 出典付きのMarkdownメモ |

公開repositoryの記述は更新される可能性があるため、出典はbranch名だけでなくcommit SHAで固定しています。
