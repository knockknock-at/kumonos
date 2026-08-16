# KUMONOS 暫定アーキテクチャ

## 1. 方針

KUMONOS本体は、入力元と出力先の双方から独立した知識編成パイプラインとする。

Codex、Claude Code、GitHub、汎用文書などはConnectorで接続し、Obsidian、JSON、HTMLなどはRendererで接続する。中核の知識モデルは、どのConnector／Rendererにも依存させない。

## 2. 全体構成

```text
Input roots
  │
  ▼
Connector ──► Normalizer ──► Sanitizer ──► Knowledge Extractor ──► Graph Resolver / Linker / Deduplicator
                                                  │                                  │
                                                  ▼                                  ▼
                                         LLM Provider Adapter                    Graph Store ◄── Manifest
                                         ├─ Direct API                               │
                                         └─ Organization Gateway                     │
                                                                                     │
                         ┌────────────────────────┼─────────────────────┐
                         ▼                        ▼                     ▼
                 Markdown Renderer       JSON / GraphML         Decision Builder
                         │                Renderer                    │
                         ▼                        └──────────┬─────────┘
                 Obsidian（任意）                           ▼
                                                  Static HTML Renderer
```

## 3. コンポーネント

### 3.1 Connector

入力形式固有の解析を担当する。

- 入力ファイルの列挙
- 共通Source／Session／Turn形式への変換
- セッションID、日時、`cwd`、役割などの保持
- 形式固有ノイズの識別

Connectorは知識抽出やMarkdown生成を行わない。

GitHub Connectorも同じ共通Source形式へ変換する。GitHub.com、GitHub Enterprise Cloud、GitHub Enterprise Serverの差は`api_base_url`、認証方式、利用可能APIの能力としてConnector内部へ閉じ込める。

```text
GitHub.com                 https://api.github.com
GitHub Enterprise Cloud   https://api.<subdomain>.ghe.com
GitHub Enterprise Server  https://<hostname>/api/v3
```

取得時はbranch名をcommit SHAへ解決し、各ファイルのblob SHAをmanifestへ保存する。GitHub上の入力を変更するAPIは使用しない。

### 3.2 Normalizer

- 文字コードと改行コードの統一
- Windows／POSIXパスの正規化
- 日本語・英語の基本的な表記正規化
- user／assistant／tool／metadataの統一表現
- 長大ログの安全な分割

### 3.3 Sanitizer

- credentialらしい文字列のマスク
- 除外パターンの適用
- LLMへ送る範囲の確定
- プロンプトインジェクション境界の付与
- 秘匿処理監査ログの出力

Sanitizerを通っていない内容を外部LLMへ送らない。

### 3.4 LLM Provider Adapter

外部LLMへの接続差を吸収し、Knowledge Extractorへ共通の結果を返す。

- `direct`：通常のAPIへ直接接続する
- `organization-gateway`：組織指定のAI Gatewayを経由する
- API形式は`responses`と`chat-completions`をadapter内部で変換する
- Base URL、モデル名、認証参照、追加header、proxy、CA bundleを接続profileとして扱う
- 接続方法が異なっても、同じ入力schema、出力schema、検証処理を使用する

Gatewayの設定内容を貼り付けて取り込む場合、貼り付け内容をPowerShellなどのプログラムとして実行しない。対応済み形式から許可した設定項目だけを抽出し、未知の命令や重複した設定はエラーにする。取り込み後の生データは保存せず、秘密値はOS資格情報ストアへ移す。

実行時にGatewayからDirect APIへ自動的に切り替えない。意図しない外部送信を防ぐため、接続失敗は明示的なエラーとして停止・再試行する。

詳細は[LLM接続の設計](llm-connection.md)を参照する。

### 3.5 Knowledge Extractor

LLMまたは決定的な抽出処理を使い、共通のKnowledge Candidateを生成する。

```text
KnowledgeCandidate
├── type
├── title
├── summary
├── body
├── aliases
├── tags
├── confidence
├── evidence
├── provenance
└── proposed_edges
```

Extractorは既存Nodeとの統合を確定せず、候補を返す。

### 3.6 Graph Resolver / Linker / Deduplicator

- aliasと既存Nodeの照合
- 類似候補の検索
- 新規作成／自動統合／レビュー送りの判定
- contradiction、supersedesなどの関係保持
- 出現ユーザー、プロジェクト、時点の集計
- 成熟度変更の提案

高confidenceであっても、`approved`以降への変更は自動確定しない。

### 3.7 Graph Store

以下を正本として保持する。

- Node
- Edge
- Provenance
- Source manifest
- Review decision
- Schema version

MVPの正本は、ローカルで配布・バックアップしやすいSQLiteとする。JSON、GraphML、Markdown、静的HTMLはすべてSQLiteから再生成する。この選択は実装開始時にADRとして記録し、入力規模の計測結果によって変更が必要か確認する。

### 3.8 Renderer

Graph Storeから派生物を生成する。

- Obsidian互換Markdown
- Portable Markdown
- JSON graph
- GraphML graph
- 判断候補データ
- 静的HTML

Rendererの生成物は削除しても再構築できる。

静的HTMLはネットワークドライブ上で直接開けるよう、Webサーバーを必須にしない。JSONとGraphMLを正本にせず、Graph Storeから再生成できる交換用データとして扱う。

### 3.9 Review Queue

以下を人間へ提示する。

- confidenceが閾値未満の統合候補
- 矛盾する知識
- `candidate-standard`への昇格候補
- 秘匿処理で要確認となった知識
- 元データより閲覧範囲が広がる可能性がある出力

### 3.10 Decision Builder

Review Queueを、人が行動を決められる単位へ変換する。

- `standardize`：正式な手順として検討する
- `resolve-conflict`：矛盾する知識を比較する
- `merge`：重複している可能性のある知識を統合する
- `verify`：利用価値は高いが根拠が不足している知識を検証する
- `reuse`：別プロジェクトへ横展開できる手順を確認する

各候補には、対象Node、候補になった理由、観測数、検証状態、注意点、推奨する次の行動を含める。単一の不透明な総合点だけで優先順位を決めず、人が判断に使った信号を確認できるようにする。

MVPの静的HTMLは閲覧専用とする。判断結果は管理者画面からローカルSQLiteへ記録する。CLIも自動運用や障害対応のために同じ処理を呼び出せる。これにより、ネットワークドライブ上のHTMLから直接データを書き換えるためのWebサーバーを不要にする。

### 3.11 Admin Console

KUMONOS実行端末で動く管理者向けのローカル画面とし、日常操作の入口をCLIではなくこの画面へ集約する。

- 初回設定ウィザード
- 参照先と出力先の登録・事前検査
- LLM接続テストと資格情報ストアへの保存
- 利用者台帳と用語集のレビュー
- 確認実行、更新して公開、状態確認
- 統合、矛盾、標準化候補の承認・保留・却下
- Windowsタスクスケジューラの設定

管理者画面はローカルホストだけで待ち受ける構成、またはデスクトップUIとして実装する。ネットワーク上へ管理APIを公開しない。静的HTMLから管理者画面やLLMを直接呼び出さない。

## 4. 中核データモデル

### Node

| フィールド | 概要 |
|---|---|
| `id` | 永続的な内部ID |
| `type` | problem、solution、failure、playbookなど |
| `title` | 人間向け名称 |
| `summary` | 短い説明 |
| `body` | 詳細内容 |
| `aliases` | 日本語、英語、略語、旧名称 |
| `lifecycle` | 知識の成熟度 |
| `confidence` | 内容と統合判断の確度 |
| `first_observed_at` | 最初の観測日時 |
| `last_observed_at` | 最後の観測日時 |
| `schema_version` | schema version |

### Edge

| フィールド | 概要 |
|---|---|
| `id` | 永続的な内部ID |
| `source_node_id` | 接続元 |
| `target_node_id` | 接続先 |
| `type` | solves、uses、contradictsなど |
| `confidence` | 関係の確度 |
| `valid_from` | 関係が有効になった時点 |
| `valid_to` | 関係が無効になった時点。任意 |

### Provenance

| フィールド | 概要 |
|---|---|
| `source_id` | 入力ファイルの識別子 |
| `session_id` | 会話セッションID |
| `source_owner` | 入力所有者またはスコープ |
| `project` | 関連プロジェクト |
| `observed_at` | 発生日時 |
| `excerpt_hash` | 抽出元範囲のハッシュ |
| `derivation` | extracted、inferred、ambiguous |
| `evidence_uri` | 成果物、テスト、READMEなど |

### Owner

| フィールド | 概要 |
|---|---|
| `owner_id` | 表示名が変わっても維持する内部ID |
| `display_name` | 実名表示が許可された場合の名称 |
| `privacy_label` | 匿名表示用の名称 |
| `organization_unit` | 部署・組織単位 |
| `aliases` | OS名、フォルダ名などの対応付け候補 |
| `active` | 現在も利用する人物か |

未割当の入力は新規人物として自動確定せず、Admin Consoleのレビュー対象とする。閲覧出力ではprofileの規則に従い、実名、匿名名、集計のみのいずれかを使う。

### Term

| フィールド | 概要 |
|---|---|
| `term_id` | 用語の内部ID |
| `canonical_label` | 承認済みの正式表記 |
| `aliases` | 略語、英語名、表記揺れ |
| `deprecated_labels` | 旧名称 |
| `suspected_misuse` | 誤用の疑いがある表記 |
| `status` | draft、approved、deprecated |
| `approved_by`／`approved_at` | 承認者と承認日時 |

元ログは改変せず、表示時に承認済み用語を使う。誤用の疑いはLLMだけで訂正せず、人間のレビューへ送る。

GitHubの出典は、表示用HTTPS URLに加えて次の形式の永続的な内部URIで表現する。

```text
github://<host>/<owner>/<repository>@<commit-sha>/<path>#L<start>-L<end>
```

## 5. 処理状態

ファイル処理と知識成熟度を混同しない。

### 入力処理状態

```text
discovered → normalized → sanitized → compiled → committed
                                   └→ failed / retryable
```

### 知識成熟度

```text
draft → observed → repeated → candidate-standard → approved → operationalized
```

入力追加・変更時は、変更したSourceから参照されるKnowledge Candidateと、その近傍Node、Edge、観測数、成熟度、Decisionだけをtransaction内で再計算する。削除されたSourceは`inactive`として根拠集計から除外し、根拠を失った承認済みNodeは削除せずレビューへ送る。

各Nodeには`schema_version`、`normalizer_version`、`prompt_version`、`glossary_version`を保持する。version変更で影響する範囲だけを再処理し、非互換schema変更や管理者の明示操作時だけ全再構築する。

## 6. 配置モデル

### 最小構成

- 1台のWindows端末でKUMONOSを定期実行する。
- 実行端末にAdmin Console、秘密値を含まない設定、OS資格情報、SQLite Graph Store、cache、log、backupを置く。
- ネットワークドライブ上の対象フォルダを読み取り、再生成可能なHTML、Markdown、JSON、GraphMLだけをネットワーク上へ公開する。
- SQLiteをネットワークドライブ上で直接更新しない。
- 一つのprofileを一つの`security_scope`に対応させ、公開、社内、限定案件のGraph Storeと出力を分ける。
- 閲覧者はブラウザで静的HTMLを開く。Obsidianは任意とする。

### 将来構成

- 管理サーバーまたは専用端末で一元実行する。
- セキュリティスコープごとに出力領域を分離する。
- 閲覧者はObsidianまたは静的HTMLを使う。
- Graph StoreをAPI経由で検索できるようにする。

配置と運用の詳細は[アプリMVPの起動・設定・運用設計](app-mvp.md)を参照する。

## 7. 入力元との境界

KUMONOSは、入力元となる製品やフォルダ構成を所有しない。利用者が設定ファイルで入力ルート、Connector、include／exclude、所有者などのmetadataを指定する。

```text
source:
  root: <任意のローカルまたはネットワークフォルダ>
  connector: <ログ形式に対応するConnector>
  include: <対象パターン>
  exclude: <除外パターン>
```

GitHub入力は、ローカルフォルダと同じ`source`の一種として設定する。設定例は[GitHub入力の設計](github-connector.md)を参照する。

特定製品向けの補助設定を将来提供する場合も、本体とは別に配布可能なサンプル設定または拡張パッケージとして扱う。製品名、固定パス、組織固有のディレクトリ規約を中核へ組み込まない。

## 8. 管理者画面と暫定CLI

管理者の通常操作はAdmin Consoleから行う。初回設定では参照先、出力先、LLM接続、利用者表示を登録し、確認実行の後に最初の公開を行う。2回目以降は「更新して公開」「結果を開く」「確認実行」「状態を確認」を主操作とする。

CLIはAdmin Consoleと同じapplication serviceを呼び出し、タスクスケジューラ、自動テスト、障害対応に利用する。

```text
kumonos init       # 設定と出力領域を初期化
kumonos scan       # 入力差分を検出
kumonos compile    # 未処理入力を知識候補へ変換
kumonos review     # レビュー待ちを確認
kumonos export     # Markdown／JSONなどを再生成
kumonos status     # 件数、エラー、利用量を表示
kumonos rebuild    # 入力からGraph Storeを再構築
```

コマンド名と引数は実装開始前にCLI仕様として確定する。

## 9. 公開手順

1. Graph StoreをローカルSQLiteのtransactionで更新する。
2. 公開物一式をネットワーク出力先の`.staging/<run-id>`へ生成する。
3. schema、リンク、必須file、秘密値混入、書込み結果を検証する。
4. 成功した場合だけ`current`へ切り替え、必要なら旧版を`history/<run-id>`へ残す。
5. 失敗時は前回成功した`current`を維持し、Admin Consoleへエラーを表示する。

静的HTMLは閲覧専用とし、MVPではLLMへの追加質問機能を持たせない。
