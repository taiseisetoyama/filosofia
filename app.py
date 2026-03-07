import streamlit as st
import google.generativeai as genai

# アプリの設定
st.set_page_config(page_title="My Philosophy AI")
st.title("My Gemini Philosophy AI")

# 1. APIキーの読み込み
if "GEMINI_API_KEY" not in st.secrets:
    st.error("SecretsにGEMINI_API_KEYが設定されていません。")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# 2. 思想データの読み込み
@st.cache_data
def load_memory():
    try:
        with open("memory.txt", "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"思想データの読み込みに失敗しました: {e}"

philosophical_context = load_memory()

# 3. モデルの初期化（安全設定を解除した1.5 Pro）
model = "models/gemini-1.5-pro",(
    model_name="gemini-1.5-pro",
    safety_settings=[
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]
)

# 4. チャット履歴の管理
if "messages" not in st.session_state:
    st.session_state.messages = []
    # 最初のシステム指示をチャットエンジンに渡す
    st.session_state.chat = model.start_chat(history=[])
    system_instruction = f"あなたは私の思想の理解者です。以下の背景を前提に対話してください：\n\n{philosophical_context}"
    st.session_state.chat.send_message(system_instruction)

# 過去のメッセージを表示
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 5. ユーザー入力
if prompt := st.chat_input("対話を開始する..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            response = st.session_state.chat.send_message(prompt, stream=True)
            full_text = ""
            placeholder = st.empty()
            for chunk in response:
                full_text += chunk.text
                placeholder.markdown(full_text + "▌")
            placeholder.markdown(full_text)
            st.session_state.messages.append({"role": "assistant", "content": full_text})
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")
