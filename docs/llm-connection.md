# KUMONOS LLM接続の設計

## 1. 目的

KUMONOSが通常のAPIと組織指定のAI Gatewayのどちらでも動き、同じ知識データ、グラフ、判断候補を生成できるようにする。

接続先ごとの違いはLLM Provider Adapterへ閉じ込め、Knowledge Extractor以降の処理へ持ち込まない。

## 2. 利用者に見せる二つの方式

### APIを直接指定

利用者または管理者が次を入力する。

- APIキー
- モデル名
- Base URL（任意）
- API形式（通常は自動判定、必要な場合だけ指定）

### 組織指定のAI Gateway

組織の管理画面で生成された設定内容を貼り付ける。

KUMONOSは貼り付け内容から、対応済みの項目だけを読み取る。

- Base URL
- モデル名またはモデルalias
- API形式
- 認証情報または認証情報の参照名
- 必要な追加header
- proxyまたはCA bundleの参照

貼り付け内容にPowerShell、コマンド、ファイル操作が含まれていても実行しない。対応済みの設定表現だけを解析し、解析できない内容は管理者へエラーとして返す。

## 3. 共通の内部仕様

Knowledge Extractorは接続先へ直接依存せず、次の共通requestをLLM Provider Adapterへ渡す。

```text
LLMRequest
├── task
├── input
├── output_schema
├── schema_version
├── trace_id
└── limits
```

Adapterは接続方式固有のAPI requestへ変換し、次の共通resultを返す。

```text
LLMResult
├── data
├── schema_version
├── model
├── usage
├── request_id
├── connection_profile_id
└── warnings
```

`data`はDirect APIとGatewayで同じJSON Schemaに適合しなければならない。schema違反は自動修正で隠さず、再試行可能な検証エラーとして扱う。

## 4. 対応するAPI形式

MVPのadapterは次を扱う。

| API形式 | 用途 |
|---|---|
| `responses` | Structured Outputsを利用できる通常の第一候補 |
| `chat-completions` | OpenAI互換Gatewayで必要な場合の互換経路 |

`chat-completions`を使用する場合も、返却されたJSONを共通schemaで検証してから中核へ渡す。API形式の違いによってNode、Edge、provenanceの定義を変えない。

## 5. 設定profile

設定ファイルには秘密値を書かず、OS資格情報ストアの参照名だけを保存する。

### Direct APIの例

```yaml
llm:
  connection_profile: direct-production

llm_profiles:
  direct-production:
    mode: direct
    adapter: openai
    api_style: responses
    base_url: https://api.openai.com/v1
    credential_ref: os-keyring://kumonos/direct-production
    models:
      extract: configured-extract-model
      judge: configured-judge-model
```

### 組織指定のAI Gatewayの例

```yaml
llm:
  connection_profile: organization-production

llm_profiles:
  organization-production:
    mode: organization-gateway
    adapter: openai-compatible
    api_style: chat-completions
    base_url: https://ai-gateway.example.invalid/v1
    credential_ref: os-keyring://kumonos/organization-production
    models:
      extract: organization-extract-model
      judge: organization-judge-model
```

モデル名、URL、header名をプログラムへ固定しない。同じprofile IDの内容を管理者が更新できるようにする。

## 6. 設定内容の取り込み

`kumonos init`では次の流れを想定する。

1. 「APIを直接指定」または「組織指定のAI Gateway」を選ぶ。
2. Direct APIでは各入力欄へ値を入れる。
3. Gatewayでは管理画面で生成された設定内容を貼り付ける。
4. KUMONOSが許可した項目だけを解析し、接続先、API形式、モデルを確認画面へ表示する。
5. 秘密値をOS資格情報ストアへ保存する。
6. 貼り付けた原文と画面上の秘密値を破棄する。
7. 業務文書を送らない接続テストを行う。

設定importerは、匿名化した実物fixtureで互換性を検証する。fixtureへ実際のAPIキー、社内host、個人名を含めない。

## 7. 安全上の要件

- Sanitizerを通過していない内容を、どちらの方式でも送信しない。
- Gateway失敗時にDirect APIへ自動fallbackしない。
- APIキー、token、追加headerの値をログへ出さない。
- 接続先hostを管理者の許可リストで制限する。
- TLS証明書検証を無効化しない。独自CAは明示的なbundle参照で扱う。
- 設定の貼り付け内容を、PowerShellやshellとして実行しない。
- 静的HTML、Markdown、JSON、GraphMLへ接続情報を出力しない。

監査ログへ残すのは、接続profile ID、API形式、モデルalias、request ID、token使用量、成否だけとする。

## 8. 同じ仕様であることの確認

Direct APIとGateway adapterへ同じ匿名化fixtureと同じJSON Schemaを渡し、次を自動テストする。

1. 両方の結果が同じschema versionへ適合する。
2. Node種別と必須fieldが同じである。
3. provenanceが失われない。
4. usageとrequest IDが共通resultへ正規化される。
5. 認証情報や接続先固有の値が生成物へ混入しない。

文章表現まで完全一致させるのではなく、KUMONOSが扱う構造と検証規則が同一であることを保証する。
