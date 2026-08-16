# KUMONOS MVPロードマップ

## Phase 0: 実データ確認と設計確定

目的は、想定ではなく実際のログ形式と量に基づいてMVPを設計することである。

- Codex session／rollout JSONLのサンプル調査
- Claude Code project／conversation JSONLのサンプル調査
- GitHub.com公開リポジトリのREADME／docs／tree APIのサンプル調査
- 1セッション当たりのサイズ、Turn数、ノイズ比率を計測
- credential・個人識別情報の出現パターンを確認
- 共通Session／Turn schemaを決定
- SQLiteを正本にするADRを作成し、実データ規模で妥当性を確認
- Direct APIと組織指定のAI Gatewayを共通化するLLM provider方針を決定
- 匿名化したGateway設定fixtureと、許可項目だけを読むimport仕様を決定
- 管理者画面とapplication serviceの境界を決定
- profile、`security_scope`、参照先、出力先の設定schemaを決定
- `owner_id`、実名・匿名表示、未割当処理を含む利用者台帳schemaを決定
- 正式用語、別名、旧名称、誤用候補を含む用語集schemaを決定
- ローカルGraph Storeとネットワーク公開物の配置をADRへ記録

### 完了条件

- 匿名化したテストfixtureがある
- Connector schemaが確定している
- 主要な秘匿パターンがテスト化されている
- MVPの性能・費用目標を設定できる
- 利用者表示と用語レビューの規則がfixtureで確認できる
- 一つのprofileを一つの`security_scope`へ対応付けられる

## Phase 1: ローカル知識化パイプライン

- 設定ファイル読み込み
- Windows用インストーラーまたはセットアップ手順
- デスクトップ／スタートメニューから起動する管理者画面
- 参照先、出力先、LLM接続、利用者表示の初回設定ウィザード
- 確認実行、更新して公開、結果を開く、状態確認
- 対象フォルダのscan
- 内容ハッシュによるmanifest管理
- Codex Connector
- Claude Code Connector
- GitHub Connector（公開GitHub.com、README／docs）
- Normalizer
- Sanitizer
- LLM provider interface
- Direct API adapter
- OpenAI互換Gateway adapter
- Gateway設定の安全なimport（貼り付け内容を実行しない）
- 接続方法に依存しないKnowledge Candidate schema検証
- ローカルSQLite Graph Storeとtransaction更新
- 安定した`owner_id`と未割当利用者レビュー
- 用語集による表示標準化と誤用候補レビュー
- problem／solution／failure／playbook抽出
- JSON graph出力
- GraphML出力
- Portable Markdown出力
- 判断候補データ出力
- サンプルデータを使った静的HTML出力
- `.staging/<run-id>`で検証してから`current`へ切り替える公開処理
- 管理者画面からの承認、保留、却下

### 完了条件

- 同じ入力を2回処理しても重複Nodeが増えない
- 更新されたログだけを再処理できる
- 元セッションを各Nodeから追跡できる
- Obsidianなしで処理が完了する
- ブラウザで判断候補と知識の関係を確認できる
- 公開GitHubリポジトリから生成した知識がcommitとpathへ追跡できる
- Direct APIとGateway経由で同じ出力schemaを検証できる
- 認証情報を設定、ログ、生成物へ残さない
- 閲覧者がKUMONOSやObsidianなしで`current/index.html`を開ける
- 公開に失敗しても前回成功した`current`が残る
- 利用者を実名または匿名名で一貫して表示できる
- 静的HTMLにLLMへの追加質問機能を含めない

## Phase 2: KUMONOSとしての知識統合

- alias・表記揺れ管理
- 用語集変更時の影響範囲再評価
- Node統合候補の検索
- contradiction／supersedesの保持
- provenanceとconfidenceの表示
- lifecycle集計
- `repeated`／`candidate-standard`候補の生成
- review queue
- 管理者画面のレビュー絞り込みと一括処理
- Obsidian Markdown Renderer
- 実データを使った静的HTMLの絞り込み・詳細表示
- GitHub認証、private repository、GitHub Enterprise Cloud／Server
- GitHub App認証とrepository単位のread-only権限

### 完了条件

- 複数人の同種ノウハウを一つの知識へ結び付けられる
- 自動統合とレビュー対象を区別できる
- Obsidianで知識同士の関係を閲覧できる
- 標準化候補を一覧化できる

## Phase 3: 組織運用

- Windowsタスクスケジューラ用実行設定
- 管理者画面からのスケジュール設定
- 排他制御と障害回復
- 利用量・費用上限
- 部署・アクセス範囲別の出力分離
- corporate proxy、独自CA、GitHub Enterprise Server互換性テスト
- 監査・保持期間設定
- schema migration
- バックアップ・restore手順
- profile単位の移行・復旧手順

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
- Direct API／Gatewayの接続profile形式
- Gateway設定importの対応形式と匿名化fixture
- テストfixtureの生成方法
- 外部送信を伴うテストの分離方法
- 配布方法
- インストーラーの更新、署名、アンインストール方式
