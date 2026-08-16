# KUMONOS MVPロードマップ

## Phase 0: 実データ確認と設計確定

目的は、想定ではなく実際のログ形式と量に基づいてMVPを設計することである。

- Codex session／rollout JSONLのサンプル調査
- Claude Code project／conversation JSONLのサンプル調査
- 1セッション当たりのサイズ、Turn数、ノイズ比率を計測
- credential・個人識別情報の出現パターンを確認
- 共通Session／Turn schemaを決定
- SQLiteを正本にするADRを作成し、実データ規模で妥当性を確認
- 初期LLM provider方針を決定

### 完了条件

- 匿名化したテストfixtureがある
- Connector schemaが確定している
- 主要な秘匿パターンがテスト化されている
- MVPの性能・費用目標を設定できる

## Phase 1: ローカル知識化パイプライン

- 設定ファイル読み込み
- 対象フォルダのscan
- 内容ハッシュによるmanifest管理
- Codex Connector
- Claude Code Connector
- Normalizer
- Sanitizer
- LLM provider interface
- problem／solution／failure／playbook抽出
- JSON graph出力
- GraphML出力
- Portable Markdown出力
- 判断候補データ出力
- サンプルデータを使った静的HTML出力

### 完了条件

- 同じ入力を2回処理しても重複Nodeが増えない
- 更新されたログだけを再処理できる
- 元セッションを各Nodeから追跡できる
- Obsidianなしで処理が完了する
- ブラウザで判断候補と知識の関係を確認できる

## Phase 2: KUMONOSとしての知識統合

- alias・表記揺れ管理
- Node統合候補の検索
- contradiction／supersedesの保持
- provenanceとconfidenceの表示
- lifecycle集計
- `repeated`／`candidate-standard`候補の生成
- review queue
- Obsidian Markdown Renderer
- 実データを使った静的HTMLの絞り込み・詳細表示

### 完了条件

- 複数人の同種ノウハウを一つの知識へ結び付けられる
- 自動統合とレビュー対象を区別できる
- Obsidianで知識同士の関係を閲覧できる
- 標準化候補を一覧化できる

## Phase 3: 組織運用

- Windowsタスクスケジューラ用実行設定
- 排他制御と障害回復
- 利用量・費用上限
- 部署・アクセス範囲別の出力分離
- 監査・保持期間設定
- schema migration
- バックアップ・restore手順

### 完了条件

- 管理者の常時操作なしで定期実行できる
- 失敗時に入力や既存Graph Storeを破損しない
- 閲覧権限を越えて知識を公開しない
- 運用状態と費用を管理者が確認できる

## 最初の実装候補

Phase 0の次に、以下の縦切りを最初の実行可能プロトタイプとする。

1. 一つのCodex rollout JSONLを読み込む
2. user／assistantの本文だけを抽出する
3. credentialらしい文字列をマスクする
4. LLMへ構造化抽出を依頼する
5. problem／solution／failure／playbookをJSONへ保存する
6. provenance付きMarkdownへ変換する
7. 同じファイルを再実行しても重複しないことをテストする

この縦切りで、入力、秘匿、LLM、知識schema、出力、冪等性というKUMONOSの主要リスクを一度に検証する。

## 実装開始前に決めること

- 実装言語
- CLI framework
- 設定ファイル形式
- Graph Store
- 初期LLM provider
- テストfixtureの生成方法
- 外部送信を伴うテストの分離方法
- 配布方法
