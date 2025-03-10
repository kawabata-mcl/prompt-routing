import boto3
import time

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
        "topP": 1.0
    }
    
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
            return "haiku"
        elif model_choice_text == "1":
            return "sonnet"
        else:
            # 想定外の応答の場合はデフォルト値を返す
            print(f"Nova Liteから想定外の応答がありました: {model_choice_text}")
            return "sonnet"  # デフォルトはsonnetを選択
    
    except Exception as e:
        print(f"Nova Lite呼び出し中にエラーが発生しました: {e}")
        # エラー発生時はsonnetをフォールバックとして使用
        return "sonnet"

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
    
    try:
        # 選択したClaudeモデルを呼び出し
        response = bedrock_runtime.converse(
            modelId=MODEL_ID,
            messages=messages,
            inferenceConfig=inference_config
        )
        
        # 応答テキストを取得して返す
        return response["output"]["message"]["content"][0]["text"]
    
    except Exception as e:
        print(f"Claude モデル呼び出し中にエラーが発生しました: {e}")
        return f"エラーが発生しました: {e}"

def route_and_process(prompt_text):
    """
    プロンプトをルーティングして処理する
    """
    # Nova Liteでプロンプトを分析
    model_choice = analyze_prompt_with_nova(prompt_text)
    
    # モデル選択結果を表示
    model_name = "Claude 3.5 Haiku" if model_choice == "haiku" else "Claude 3.7 Sonnet"
    print(f"選択されたモデル: {model_name}")
    
    # 選択されたモデルを呼び出し
    response = invoke_claude_model(prompt_text, model_choice)
    
    # 結果を返す
    return response

# ユーザー入力を受け取って処理する
if __name__ == "__main__":
    print("プロンプトルーティングシステム（シンプル版）")
    print("終了するには 'exit' または 'quit' と入力してください")
    print("-" * 50)
    
    while True:
        # ユーザーからのプロンプト入力を受け取る
        user_prompt = input("\nプロンプトを入力してください: ")
        
        # 終了条件をチェック
        if user_prompt.lower() in ['exit', 'quit']:
            print("プログラムを終了します")
            break
        
        # 入力が空の場合はスキップ
        if not user_prompt.strip():
            print("プロンプトが入力されていません。もう一度入力してください。")
            continue
        
        # プロンプトを処理して結果を表示
        print("\n処理中...\n")
        response = route_and_process(user_prompt)
        print("\n回答:\n")
        print(response)
        print("\n" + "-" * 50) 