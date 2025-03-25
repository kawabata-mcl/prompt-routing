import boto3
import json
import time
import os
import datetime

# Bedrockクライアントの初期化
bedrock_runtime = boto3.client(
    service_name="bedrock-runtime",
    region_name="us-east-1"
)

def analyze_prompt_with_nova(prompt_text):
    """
    Amazon Nova Liteを使用してプロンプトを分析し、適切なモデルを判断する
    """
    # Nova Liteのモデルを指定
    NOVA_LITE_MODEL_ID = "us.amazon.nova-lite-v1:0"
    
    # Nova Liteへの問い合わせ内容
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "text": f"""以下のユーザープロンプトを分析し、処理に適したモデルを選択してください。

プロンプト: {prompt_text}

判断基準:
- 複雑で詳細な回答が必要な場合は「1」
- 簡潔で基本的な回答で十分な場合は「0」

複雑な回答が必要な場合（1を選択）:
- 詳細な説明や分析が必要
- 高度な推論や創造的なタスク
- 複数の観点からの考察
- 長文の生成が必要

簡潔な回答で十分な場合（0を選択）:
- 基本的な質問応答
- 短い返答で済むもの
- 事実の確認程度のもの
- 単純なタスク

回答は必ず「0」または「1」のみで答えてください。それ以外の文字や説明は不要です。"""
                }
            ]
        }
    ]
    
    # 推論パラメータ（最大トークン数を減らす）
    inference_config = {
        "maxTokens": 5,  # 非常に短い回答のみ必要
        "temperature": 0.0,  # 決定的な回答を得るため最低温度を設定
    }
    
    start_time = time.time()
    try:
        # Nova Liteモデルを呼び出し
        response = bedrock_runtime.converse(
            modelId=NOVA_LITE_MODEL_ID,
            messages=messages,
            inferenceConfig=inference_config
        )
        
        # 応答からモデル選択を抽出
        model_choice_text = response["output"]["message"]["content"][0]["text"].strip()
        
        # 「0」または「1」の応答を「haiku」または「sonnet」に変換
        if model_choice_text == "0":
            model_choice = "haiku"
        elif model_choice_text == "1":
            model_choice = "sonnet"
        else:
            # 想定外の応答の場合はデフォルト値を返す
            print(f"Nova Liteから想定外の応答がありました: {model_choice_text}")
            model_choice = "sonnet"  # デフォルトはsonnetを選択
        
        elapsed_time = time.time() - start_time
        
        # 消費トークン数を取得
        input_tokens = response.get("usage", {}).get("inputTokens", 0)
        output_tokens = response.get("usage", {}).get("outputTokens", 0)
        
        result = {
            "model_choice": model_choice,
            "original_response": model_choice_text,
            "elapsed_time": elapsed_time,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "response": response
        }
        
        return result
    
    except Exception as e:
        print(f"Nova Lite呼び出し中にエラーが発生しました: {e}")
        # エラー発生時はsonnetをフォールバックとして使用
        return {
            "model_choice": "sonnet",  # フォールバックモデルをsonnetに設定
            "original_response": "エラー",
            "elapsed_time": time.time() - start_time,
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "error": str(e)
        }

def invoke_claude_model(prompt_text, model_choice):
    """
    選択されたClaudeモデルを呼び出す
    """
    # モデルIDを設定
    if model_choice == "haiku":
        MODEL_ID = "us.anthropic.claude-3-5-haiku-20241022-v1:0"
    else:  # sonnet
        MODEL_ID = "us.anthropic.claude-3-5-sonnet-20241022-v2:0"
    
    # メッセージの構成
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "text": prompt_text
                }
            ]
        }
    ]
    
    # 推論パラメータ
    inference_config = {
        "maxTokens": 4096,
        "temperature": 0.7,
        "topP": 0.9
    }
    
    start_time = time.time()
    try:
        # 選択したClaudeモデルを呼び出し
        response = bedrock_runtime.converse(
            modelId=MODEL_ID,
            messages=messages,
            inferenceConfig=inference_config
        )
        
        # 応答テキストを取得
        response_text = response["output"]["message"]["content"][0]["text"]
        
        elapsed_time = time.time() - start_time
        
        # 消費トークン数を取得
        input_tokens = response.get("usage", {}).get("inputTokens", 0)
        output_tokens = response.get("usage", {}).get("outputTokens", 0)
        
        result = {
            "response_text": response_text,
            "elapsed_time": elapsed_time,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "response": response
        }
        
        return result
    
    except Exception as e:
        print(f"Claude モデル呼び出し中にエラーが発生しました: {e}")
        return {
            "response_text": f"エラーが発生しました: {e}",
            "elapsed_time": time.time() - start_time,
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "error": str(e)
        }

def save_results(prompt_text, nova_result, claude_result, final_response):
    """
    実行結果をマークダウンファイルとして保存する
    """
    # resultsディレクトリがなければ作成
    os.makedirs("results", exist_ok=True)
    
    # 現在の日時を取得してファイル名に使用
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"results/result_{timestamp}.md"
    
    # Nova Liteのエラー情報
    nova_error = nova_result.get("error", "なし")
    
    # Nova Liteの出力テキストを取得
    nova_output_text = nova_result.get("original_response", "取得できませんでした")
    
    # Nova Liteのモデル選択結果
    model_choice = nova_result.get("model_choice", "不明")
    
    # Claudeモデルのエラー情報
    claude_error = claude_result.get("error", "なし")
    
    # マークダウン形式で結果を作成
    markdown_content = f"""# プロンプト処理結果 - {timestamp}

## 入力プロンプト

```
{prompt_text}
```

## Nova Lite分析結果

- **選択モデル**: {"Claude 3.7 Sonnet" if model_choice == "sonnet" else "Claude 3.5 Haiku"}
- **処理時間**: {round(nova_result.get("elapsed_time", 0), 2)}秒
- **入力トークン数**: {nova_result.get("input_tokens", 0)}
- **出力トークン数**: {nova_result.get("output_tokens", 0)}
- **合計トークン数**: {nova_result.get("total_tokens", 0)}
- **エラー**: {nova_error}

### Nova Lite出力テキスト

```
{nova_output_text} (0=Haiku, 1=Sonnet)
```

### 分類結果

```
{model_choice}
```

## Claudeモデル実行結果

- **使用モデル**: {"Claude 3.7 Sonnet" if model_choice == "sonnet" else "Claude 3.5 Haiku"}
- **処理時間**: {round(claude_result.get("elapsed_time", 0), 2)}秒
- **入力トークン数**: {claude_result.get("input_tokens", 0)}
- **出力トークン数**: {claude_result.get("output_tokens", 0)}
- **合計トークン数**: {claude_result.get("total_tokens", 0)}
- **エラー**: {claude_error}

## 最終応答

```
{final_response}
```
"""
    
    # マークダウンファイルとして保存
    with open(filename, "w", encoding="utf-8") as f:
        f.write(markdown_content)
    
    print(f"実行結果を {filename} に保存しました")
    return filename

def process_prompt(prompt_text):
    """
    プロンプトを処理し、適切なモデルを選択して結果を返す
    """
    # Nova Liteでプロンプトを分析
    nova_result = analyze_prompt_with_nova(prompt_text)
    model_choice = nova_result.get("model_choice")
    
    print(f"選択されたモデル: Claude 3.{'5' if model_choice == 'haiku' else '7 '}{'Haiku' if model_choice == 'haiku' else 'Sonnet'}")
    print(f"Nova Lite処理時間: {round(nova_result.get('elapsed_time', 0), 2)}秒")
    print(f"Nova Lite消費トークン: {nova_result.get('total_tokens', 0)}トークン")
    
    # 選択されたモデルを呼び出し
    claude_result = invoke_claude_model(prompt_text, model_choice)
    final_response = claude_result.get("response_text")
    
    print(f"Claude処理時間: {round(claude_result.get('elapsed_time', 0), 2)}秒")
    print(f"Claude消費トークン: {claude_result.get('total_tokens', 0)}トークン")
    
    # 結果を保存
    save_results(prompt_text, nova_result, claude_result, final_response)
    
    return final_response

# 使用例
if __name__ == "__main__":
    # テストプロンプトを外部ファイルから読み込み
    try:
        from test_prompts import test_prompts
        print(f"テストプロンプトを読み込みました: {len(test_prompts)}件")
    except ImportError:
        print("警告: test_prompts.py が見つかりません。デフォルトのプロンプトを使用します。")
        # デフォルトのプロンプト（ファイルが見つからなかった場合のフォールバック）
        test_prompts = [
            "こんにちは",
            "量子コンピューティングについて詳しく説明してください。",
        ]
    
    # 動作モード
    # True: すべてのプロンプトを順番に処理
    # False: 選択したプロンプトのみ処理
    process_all_prompts = True
    
    if process_all_prompts:
        # すべてのプロンプトを順番に処理
        for i, prompt in enumerate(test_prompts):
            print(f"\n\n===== プロンプト {i+1}/{len(test_prompts)} =====")
            print(f"プロンプト: {prompt}")
            print("=" * 40)
            
            response = process_prompt(prompt)
            
            print("\n----- 回答 -----")
            print(response)
            print("=" * 40)
    else:
        # 1つのプロンプトのみ処理
        selected_prompt_index = 0  # プロンプトインデックスを選択
        
        # インデックスの範囲チェック
        if selected_prompt_index < 0 or selected_prompt_index >= len(test_prompts):
            print(f"警告: 選択したインデックス {selected_prompt_index} は範囲外です。インデックス 0 を使用します。")
            selected_prompt_index = 0
            
        user_prompt = test_prompts[selected_prompt_index]
        
        print(f"選択したプロンプト: {user_prompt}")
        response = process_prompt(user_prompt)
        print("\n回答:\n", response)
