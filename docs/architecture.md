# KUMONOS 暫定アーキテクチャ

## 1. 方針

KUMONOS本体は、入力元と出力先の双方から独立した知識編成パイプラインとする。

Codex、Claude Code、汎用文書などはConnectorで接続し、Obsidian、JSON、HTMLなどはRendererで接続する。中核の知識モデルは、どのConnector／Rendererにも依存させない。

## 2. 全体構成

```text
Input roots
  │
  ▼
Connector ──► Normalizer ──► Sanitizer ──► Knowledge Extractor
                                                  │
                                                  ▼
Manifest ◄────────────── Graph Resolver / Linker / Deduplicator
  │                                               │
  │                                               ▼
  └──────────────────────────────────────────► Graph Store
                                                  │
                         ┌────────────────────────┼─────────────────────┐
                         ▼                        ▼                     ▼
                 Markdown Renderer         JSON Renderer       Review Queue
                         │
                         ▼
                 Obsidian（任意）
```

## 3. コンポーネント

### 3.1 Connector

入力形式固有の解析を担当する。

- 入力ファイルの列挙
- 共通Source／Session／Turn形式への変換
- セッションID、日時、`cwd`、役割などの保持
- 形式固有ノイズの識別

Connectorは知識抽出やMarkdown生成を行わない。

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

### 3.4 Knowledge Extractor

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

### 3.5 Graph Resolver / Linker / Deduplicator

- aliasと既存Nodeの照合
- 類似候補の検索
- 新規作成／自動統合／レビュー送りの判定
- contradiction、supersedesなどの関係保持
- 出現ユーザー、プロジェクト、時点の集計
- 成熟度変更の提案

高confidenceであっても、`approved`以降への変更は自動確定しない。

### 3.6 Graph Store

以下を正本として保持する。

- Node
- Edge
- Provenance
- Source manifest
- Review decision
- Schema version

初期候補はローカルで配布・バックアップしやすいSQLiteとする。ただし、正式決定はサンプルログを使ったMVP設計時のADRで行う。

### 3.7 Renderer

Graph Storeから派生物を生成する。

- Obsidian互換Markdown
- Portable Markdown
- JSON graph
- 標準化候補レポート
- 将来：GraphML、静的HTML

Rendererの生成物は削除しても再構築できる。

### 3.8 Review Queue

以下を人間へ提示する。

- confidenceが閾値未満の統合候補
- 矛盾する知識
- `candidate-standard`への昇格候補
- 秘匿処理で要確認となった知識
- 元データより閲覧範囲が広がる可能性がある出力

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

## 6. 配置モデル

### 最小構成

- 1台のWindows端末でKUMONOSを定期実行する。
- ネットワークドライブ上の対象フォルダを読み取る。
- 一つの出力フォルダへGraph StoreとMarkdownを生成する。
- 必要なら同じ端末にObsidianを導入して確認する。

### 将来構成

- 管理サーバーまたは専用端末で一元実行する。
- セキュリティスコープごとに出力領域を分離する。
- 閲覧者はObsidianまたは静的HTMLを使う。
- Graph StoreをAPI経由で検索できるようにする。

## 7. 入力元との境界

KUMONOSは、入力元となる製品やフォルダ構成を所有しない。利用者が設定ファイルで入力ルート、Connector、include／exclude、所有者などのmetadataを指定する。

```text
source:
  root: <任意のローカルまたはネットワークフォルダ>
  connector: <ログ形式に対応するConnector>
  include: <対象パターン>
  exclude: <除外パターン>
```

特定製品向けの補助設定を将来提供する場合も、本体とは別に配布可能なサンプル設定または拡張パッケージとして扱う。製品名、固定パス、組織固有のディレクトリ規約を中核へ組み込まない。

## 8. 暫定CLI

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
