import streamlit as st
import google.generativeai as genai

# アプリの設定
st.set_page_config(page_title="My Philosophy AI", layout="centered")
st.title("My Gemini Philosophy AI")

# 1. APIキーの確認
if "GEMINI_API_KEY" not in st.secrets:
    st.error("SecretsにGEMINI_API_KEYが設定されていません。")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# 2. 思想データの読み込み（memory.txt）
@st.cache_data
def load_memory():
    try:
        with open("memory.txt", "r", encoding="utf-8") as f:
            return f.read()
    except:
        return "思想データがありません。"

philosophical_context = load_memory()

# 3. モデルの初期化
# 最も確実なモデル名「models/gemini-1.5-flash-latest」を指定します
model = genai.GenerativeModel(
    model_name="models/gemini-1.5-flash-latest",
    system_instruction=f"あなたは私の思想の理解者です。以下の背景を前提に対話してください：\n\n{philosophical_context}"
)

# 4. 会話の管理
if "messages" not in st.session_state:
    st.session_state.messages = []
    # ここでの不要な通信（send_message）を完全に削除しました
    st.session_state.chat = model.start_chat(history=[])

# 過去の履歴を表示
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 5. チャット入力欄
if prompt := st.chat_input("思考の続きを..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            # 返答を生成
            response = st.session_state.chat.send_message(prompt)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"エラーが発生しました。APIキーまたはモデル名の問題の可能性があります：\n{e}")
