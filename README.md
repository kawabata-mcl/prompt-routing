# プロンプトルーティングシステム

このプロジェクトは、入力されたプロンプトを分析し、クエリの複雑さに基づいて適切なAIモデル（Claude 3.5 HaikuまたはClaude 3.7 Sonnet）に転送するシステムです。

## 機能

- Amazon Nova Liteを使用してプロンプトの複雑さを分析
- 分析結果に基づいて適切なClaudeモデルを選択
- Nova Lite呼び出し失敗時のフォールバック処理（デフォルトはSonnet）
- 処理結果（消費トークン数、レスポンスタイムなど）の記録
- 実行結果をマークダウンファイルとして保存

## セットアップ方法

### 前提条件

- Python 3.8以上
- AWS アカウントと適切なIAM権限
- AWS CLI設定済み

### インストール方法

1. リポジトリをクローン

```bash
git clone https://github.com/kawabata-mcl/prompt-routing.git
cd prompt-routing
```

2. Python仮想環境（venv）を作成してアクティベート

```bash
# Linux/macOS
python -m venv .venv
source .venv/bin/activate

# Windows
python -m venv .venv
.venv\Scripts\activate
```

3. 依存関係をインストール

```bash
pip install -r requirements.txt
```

4. AWS認証情報を設定（AWS CLIで設定していない場合）

```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_REGION=us-east-1
```

## 使用方法

仮想環境をアクティベートしてから実行してください：

```bash
# 仮想環境をアクティベート
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# スクリプトを実行
python prompt_routing.py
```

プロンプトを入力すると、システムが適切なモデルを選択して応答します。
実行結果は `results` フォルダに保存されます。

### プロンプトの変更方法

テストプロンプトは `test_prompts.py` ファイルで管理されています。すべてのプロンプトは単一の `test_prompts` リストに保存され、コメントでプロンプトの種類が示されています：

```python
# プロンプト集（コメントでHaiku/Sonnetの適性を示します）
test_prompts = [
    # 簡単な質問（Haikuに適したプロンプト）
    "こんにちは",
    "Pythonで1から10までの数字を出力するシンプルなfor文を書いてください",
    
    # 複雑な質問（Sonnetに適したプロンプト）
    """量子コンピューティングが金融市場のアルゴリズム取引に与える影響について、
    技術的な観点と倫理的な観点から詳細に分析してください。""",
    
    # カスタム追加用
    """ここに新しいプロンプトを追加できます。
    長文の場合は複数行の文字列として記述できます。"""
]
```

新しいプロンプトを追加するには、`test_prompts` リストに直接追加してください。

`prompt_routing.py` でプロンプトを処理する方法：

```python
# 動作モード
process_all_prompts = False  # Trueに変更するとすべてのプロンプトを順番に処理

if not process_all_prompts:
    selected_prompt_index = 0  # 処理するプロンプトのインデックスを指定
```

- `process_all_prompts = True` に変更すると、すべてのプロンプトを順番に処理します
- `selected_prompt_index` を変更して、特定のプロンプトを選択できます

## 出力ファイル

実行結果は以下の形式でマークダウンファイルとして保存されます：

~~~markdown
# プロンプト処理結果 - 20240310_123456

## 入力プロンプト

```
入力されたプロンプト
```

## Nova Lite分析結果

- **選択モデル**: Claude 3.7 Sonnet/Claude 3.5 Haiku
- **処理時間**: 0.5秒
- **入力トークン数**: 100
- **出力トークン数**: 10
- **合計トークン数**: 110
- **エラー**: なし

### Nova Lite出力テキスト

```
1 (0=Haiku, 1=Sonnet)
```

### 分類結果

```
sonnet
```

## Claudeモデル実行結果

- **使用モデル**: Claude 3.7 Sonnet/Claude 3.5 Haiku
- **処理時間**: 2.5秒
- **入力トークン数**: 100
- **出力トークン数**: 200
- **合計トークン数**: 300
- **エラー**: なし

## 最終応答

```
Claudeモデルからの応答
```
~~~

### prompt_routing_simple.pyの使用方法

このプロジェクトには、詳細なログ機能を省略したシンプル版の`prompt_routing_simple.py`も含まれています。こちらは対話型のコマンドラインインターフェイスを提供し、プロンプトを入力するごとに即時に処理結果を返します。

特徴：
- コマンドライン上でシンプルな対話式インターフェイスを提供
- プロンプト入力から適切なモデル（HaikuまたはSonnet）を自動選択
- 処理結果をリアルタイムで表示
- ファイル出力機能はなし（ターミナルに直接表示のみ）

使用方法：

```bash
# 仮想環境をアクティベート
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# シンプル版スクリプトを実行
python prompt_routing_simple.py

# プロンプト入力画面が表示されるので、質問や指示を入力
# 終了するには「exit」または「quit」と入力
```

実行すると、以下のような対話型インターフェイスが起動します：

```
プロンプトルーティングシステム（シンプル版）
終了するには 'exit' または 'quit' と入力してください
--------------------------------------------------

プロンプトを入力してください: ここに質問や指示を入力

処理中...

選択されたモデル: Claude 3.5 Haiku

回答:

AIからの回答がここに表示されます

--------------------------------------------------
```
