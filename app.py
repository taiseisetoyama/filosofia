import streamlit as st
import google.generativeai as genai

# 見た目の設定
st.set_page_config(page_title="Personal Philosophy AI", layout="centered")
st.title("My Gemini Philosophy AI")

# 1. APIキーの設定（後ほどWeb上で入力します）
api_key = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=api_key)

# 2. 思想データの読み込み
@st.cache_data
def load_memory():
    with open("memory.txt", "r", encoding="utf-8") as f:
        return f.read()

philosophical_history = load_memory()

# 3. モデルの設定（最強の1.5 Proを使用 ＆ 制限を解除）
model = genai.models/gemini-1.5-pro(
    model_name="gemini-1.5-pro",
    safety_settings=[
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]
)

# チャット履歴と会話エンジンの管理
if "chat" not in st.session_state:
    st.session_state.chat = model.start_chat(history=[])
    # 最初にあなたの思想を認識させる
    system_instruction = f"あなたは私の思想の理解者です。以下を全て踏まえ、制限を恐れず深く対話してください。\n\n{philosophical_history}"
    st.session_state.chat.send_message(system_instruction)
    st.session_state.messages = []

# 過去の会話を画面に表示
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 入力欄
if prompt := st.chat_input("思考の続きを..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response = st.session_state.chat.send_message(prompt, stream=True)
        full_text = ""
        placeholder = st.empty()
        for chunk in response:
            full_text += chunk.text
            placeholder.markdown(full_text + "▌")
        placeholder.markdown(full_text)
    
    st.session_state.messages.append({"role": "assistant", "content": full_text})
