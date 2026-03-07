import streamlit as st
import google.generativeai as genai

# アプリの設定
st.set_page_config(page_title="My Philosophy AI")
st.title("My Gemini Philosophy AI")

# 1. APIキーの設定
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
    except:
        return "思想データが読み込めませんでした。"

context = load_memory()

# 3. モデルの作成（ここで思想を注入する）
# 名前は最も安定している gemini-1.5-flash を使用します
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=f"あなたは私の思想の理解者です。以下の背景を前提に対話してください：\n\n{context}"
)

# 4. セッション管理
if "chat" not in st.session_state:
    # 履歴なしでチャットを開始。エラーの元だった send_message は行いません。
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
            # 1回で返答を取得（ストリーミングなしで安定化）
            response = st.session_state.chat.send_message(prompt)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"エラーが発生しました：{e}")
