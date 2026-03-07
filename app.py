import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="My Philosophy AI")
st.title("My Gemini Philosophy AI")

# 1. APIキーの設定
if "GEMINI_API_KEY" not in st.secrets:
    st.error("Secretsにキーが設定されていません。")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# 2. 思想データの読み込み
@st.cache_data
def load_memory():
    try:
        with open("memory.txt", "r", encoding="utf-8") as f:
            return f.read()
    except:
        return ""

context = load_memory()

# 3. モデルの作成（最新の書き方：system_instruction を使用）
# ここでエラーが出るのを防ぐため、最も安定した指定方法をとります
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=f"あなたは私の思想の理解者です。以下を前提に対話してください：\n\n{context}"
)

# 4. セッション管理
if "chat" not in st.session_state:
    # 以前エラーが出ていた 45行目の send_message を完全に削除しました。
    # チャットを開始するだけで、ここでは通信を行いません。
    st.session_state.chat = model.start_chat(history=[])
if "messages" not in st.session_state:
    st.session_state.messages = []

# 過去の履歴を表示
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 5. 入力欄
if prompt := st.chat_input("対話を開始..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            # 入力があった時だけ初めて通信します
            response = st.session_state.chat.send_message(prompt)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"エラーが発生しました：{e}")
