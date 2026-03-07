import streamlit as st
import google.generativeai as genai

# 1. ページ設定
st.set_page_config(page_title="My Philosophy AI", layout="centered")
st.title("My Gemini Philosophy AI")

# 2. APIキーの設定（Secretsから読み込み）
if "GEMINI_API_KEY" not in st.secrets:
    st.error("StreamlitのSecretsにキーを設定してください。")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# 3. 思想データの読み込み
@st.cache_data
def load_memory():
    try:
        with open("memory.txt", "r", encoding="utf-8") as f:
            return f.read()
    except:
        return ""

philosophical_context = load_memory()

# 4. モデルの初期化
# 最も安定している「gemini-1.5-flash」を使用します。
# 思想データを最初からAIの「前提」として組み込みます。
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=f"あなたは私の思想の理解者です。以下を前提に対話してください：\n\n{philosophical_context}"
)

# 5. セッション（会話履歴）の管理
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.chat = model.start_chat(history=[])

# 履歴の表示
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 6. 入力欄と実行
if prompt := st.chat_input("思考の続きを..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            # 返答生成
            response = st.session_state.chat.send_message(prompt)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")
