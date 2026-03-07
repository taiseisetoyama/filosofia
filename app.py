import streamlit as st
import google.generativeai as genai

# 1. ページ基本設定
st.set_page_config(page_title="Deep Mind AI", layout="centered")
st.title("My Recursive Evolution AI")

# 2. API設定
if "GEMINI_API_KEY" not in st.secrets:
    st.error("SecretsにGEMINI_API_KEYを設定してください。")
    st.stop()
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# 3. ブラウザ上の記憶（Session State）の初期化
if "philosophy_base" not in st.session_state:
    try:
        with open("memory.txt", "r", encoding="utf-8") as f:
            st.session_state.philosophy_base = f.read()
    except:
        st.session_state.philosophy_base = "初期状態：対話を通じて思想を構築します。"

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 【重要】モデルの動的取得ロジック ---
if "target_model" not in st.session_state:
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        # 優先順位: 1.5-flash -> 1.5-flash-latest -> gemini-pro -> 最初に見つかったもの
        candidates = ["models/gemini-1.5-flash", "models/gemini-1.5-flash-latest", "models/gemini-pro"]
        st.session_state.target_model = next((c for c in candidates if c in available_models), available_models[0])
    except Exception as e:
        st.error(f"モデルの取得に失敗しました: {e}")
        st.stop()

# 4. 記憶の「再構築・圧縮」関数
def re_encode_philosophy(current_base, recent_messages):
    context = "\n".join([f"{m['role']}: {m['content']}" for m in recent_messages])
    compress_prompt = f"""
    あなたはユーザーの思想の守護者です。現在の【思想ベース】に、直近の【新しい対話】から得られた知見を統合し、より洗練された体系としてまとめ直してください。
    【現在の思想ベース】:\n{current_base}\n【新しい対話】:\n{context}
    """
    # 取得した正しいモデル名を使用
    model = genai.GenerativeModel(st.session_state.target_model)
    result = model.generate_content(compress_prompt)
    return result.text

# 5. モデルの構築（常に最新の思想ベースをシステム命令に焼き付ける）
model = genai.GenerativeModel(
    model_name=st.session_state.target_model,
    system_instruction=f"あなたは私の思想の理解者です。以下の【進化し続ける思想体系】を前提としてください：\n\n{st.session_state.philosophy_base}"
)
chat = model.start_chat(history=[])

# 6. 履歴表示
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 7. 対話実行
if prompt := st.chat_input("思考を統合せよ..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            response = chat.send_message(prompt)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
            if len(st.session_state.messages) >= 20:
                with st.spinner("思想を再エンコード中..."):
                    new_base = re_encode_philosophy(st.session_state.philosophy_base, st.session_state.messages)
                    st.session_state.philosophy_base = new_base
                    st.session_state.messages = st.session_state.messages[-4:]
                    st.success("思想が統合されました。")
        except Exception as e:
            st.error(f"接続エラー: {e}")

# 8. スマホでもセーブしやすくするための追加パーツ
st.divider()
with st.expander("💾 現在の思想（セーブ用）"):
    st.code(st.session_state.philosophy_base)

with st.sidebar:
    st.write(f"使用中モデル: {st.session_state.target_model}")
    st.subheader("現在のAI内部OS（記憶）")
    st.write(st.session_state.philosophy_base)
