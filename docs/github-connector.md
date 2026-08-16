# KUMONOS GitHub入力の設計

## 1. 目的

ローカルフォルダに加えて、GitHubリポジトリに蓄積されたREADME、設計書、運用手順、設定、選択したソースコードから知識を抽出する。

KUMONOSはGitHubへ書き込まない。Issue作成、commit、push、設定変更はGitHub Connectorの責務に含めない。

## 2. 対応範囲

同じConnectorで次を扱う。

| 種類 | URLの例 | MVP方針 |
|---|---|---|
| GitHub.com | `https://github.com` | 公開リポジトリは認証なしでも利用可能 |
| GitHub Enterprise Cloud | `https://<subdomain>.ghe.com` | 専用API URLと認証を設定 |
| GitHub Enterprise Server | `https://github.example.jp` | `api_base_url`を`/api/v3`まで設定 |

GitHubのホスト名をプログラム内へ固定しない。Web URL、API URL、認証、TLS設定を一つの接続先として管理する。

## 3. MVPで読み取るもの

初期設定では次を対象にする。

- repository metadata
- default branchまたは指定branch
- `README*`
- `docs/**/*.md`
- `**/*.md`、`**/*.txt`
- `.github/workflows/*.{yml,yaml}`
- 明示的にincludeされた小さな設定ファイルとソースコード

初期設定では次を除外する。

- binary、画像、動画
- build成果物、vendor、`node_modules`
- Git LFSの実体
- submoduleの中身
- secret、credential、`.env`
- 100 MBを超えるファイル

Issue、Pull Request、Discussion、Actions logはMVP対象外とする。repository contentとは更新頻度、権限、量、個人情報の扱いが異なるため、後から別の入力種別として追加する。

## 4. 設定例

設定形式は実装開始前に確定する。以下は意味を示す暫定YAMLである。

```yaml
sources:
  - id: public-products
    type: github
    web_base_url: https://github.com
    api_base_url: https://api.github.com
    auth:
      type: anonymous
    repositories:
      - knockknock-at/kumonos
      - knockknock-at/lifeloop
      - ganase/aiagent_workspace
    include:
      - README*
      - docs/**/*.md
      - .github/workflows/*.yml
    exclude:
      - "**/.env*"
      - "**/node_modules/**"
    include_forks: false
    include_archived: false
    security_scope: public

  - id: company-github
    type: github
    web_base_url: https://github.example.jp
    api_base_url: https://github.example.jp/api/v3
    auth:
      type: github-app
      credential_ref: windows-credential:kumonos/company-github
    repositories:
      - platform/operations
      - platform/playbooks
    tls:
      ca_bundle: C:/KUMONOS/certs/company-ca.pem
    security_scope: company-internal
```

token、秘密鍵、passwordそのものを設定ファイルへ書かない。`credential_ref`にはOSの資格情報ストアなどの参照名だけを置く。

## 5. 認証

| 利用場面 | 推奨方式 |
|---|---|
| GitHub.comの公開リポジトリ | 認証なし。rate limit不足時だけread-only token |
| 少人数の試行 | fine-grained personal access token |
| 組織運用 | GitHub App installation token |
| GitHub Enterprise Server | GitHub Appを優先し、利用中のserver versionで確認 |

組織運用では、repository metadataとContentsのread-only権限だけを与える。IssueやPull Requestを追加する場合は、後から権限を分けて追加する。

認証エラー時に公開扱いへ落として処理を続けない。対象repositoryを失敗として記録し、既存の出力を勝手に削除しない。

## 6. 取得方法

MVPはREST APIを標準にする。

1. repository ID、default branch、visibilityを取得
2. branchをcommit SHAへ解決
3. Git treeから対象ファイルを列挙
4. include／excludeとサイズ制限を適用
5. file blob SHAが前回と違うものだけ取得
6. 共通Source形式へ変換
7. commit SHA、blob SHA、path、行範囲を出典として保存

Contents APIは大きなdirectoryやfileに制約があるため、再帰列挙にはGit Trees APIを使い、必要なfileだけ取得する。非常に大きいrepositoryでは、将来shallow cloneとsparse checkoutを選択できるようにする。

## 7. 差分と出典

manifestには次を保存する。

```text
host
repository_id
repository_full_name
resolved_commit_sha
path
blob_sha
security_scope
last_scanned_at
```

内部の出典URI:

```text
github://github.com/ganase/pdf2csv@<commit-sha>/app/services/pii_detector.py#L1-L80
```

画面には、閲覧者がアクセスできる場合だけHTTPSリンクを表示する。private repositoryの名称やpathが、より広い権限の出力へ漏れないようにする。

## 8. GitHub Enterprise対応で外せない点

- `api.github.com`を固定しない
- GitHub Enterprise Serverでは`https://HOSTNAME/api/v3`を受け取る
- GitHub Enterprise Cloudの専用subdomain APIを設定可能にする
- corporate proxyと独自CA bundleを設定可能にする
- serverの`/meta`と応答headerから能力を確認する
- API version差はConnector内部のcapabilityとして扱う
- GitHub Appが使えない環境でも、read-only tokenへ切り替えられる
- hostごとにrate limit、retry、監査ログを分ける

GitHub.comで動いたAPIが、すべてのGitHub Enterprise Server versionで使えるとは仮定しない。

## 9. 安全な出力分離

公開repository、社内repository、限定repositoryを一つの出力へ自動混合しない。

```text
output/
├── public/
├── company-internal/
└── restricted-project-a/
```

Nodeが複数scopeにまたがる場合、広い側には公開可能な根拠だけを出す。限定scopeのrepository名や抜粋を、公開側の「追加根拠数」から推測できる表示も避ける。

## 10. MVP受入確認

1. 公開GitHub.com repositoryからREADMEとdocsを取得できる。
2. 同じcommitを再実行したとき、LLM処理を増やさない。
3. 1ファイルだけ更新したとき、そのblobだけを再処理する。
4. 生成ノートからrepository、commit、pathへ戻れる。
5. GitHub Enterprise Serverの任意の`api_base_url`を設定できる。
6. 認証情報をログ、SQLite、HTML、Markdownへ出力しない。
7. 異なるsecurity scopeを別の出力へ分離できる。

## 11. 公式仕様への参照

- [GitHub repository contents API](https://docs.github.com/en/rest/repos/contents)
- [GitHub Enterprise Server REST API quickstart](https://docs.github.com/en/enterprise-server@latest/rest/quickstart)
- [GitHub Enterprise Server authentication](https://docs.github.com/en/enterprise-server@latest/rest/authentication)
