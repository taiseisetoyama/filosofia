import streamlit as st
import google.generativeai as genai

# 基本設定
st.set_page_config(page_title="Philosophy AI")
st.title("My Gemini Philosophy AI")

# APIキー設定
if "GEMINI_API_KEY" not in st.secrets:
    st.error("SecretsにGEMINI_API_KEYを設定してください。")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# 思想データの読み込み
@st.cache_data
def load_memory():
    try:
        with open("memory.txt", "r", encoding="utf-8") as f:
            return f.read()
    except:
        return ""

# モデル設定 (NotFoundを避けるためflashモデルを使用)
if "chat" not in st.session_state:
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=f"あなたは私の思想の理解者です：\n\n{load_memory()}"
    )
    st.session_state.chat = model.start_chat(history=[])
    st.session_state.messages = []

# 履歴表示
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 対話入力
if prompt := st.chat_input("対話を開始..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            response = st.session_state.chat.send_message(prompt)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"エラー: {e}")
