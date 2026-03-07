import streamlit as st
import google.generativeai as genai

# --- ページ設定 ---
st.set_page_config(page_title="My Philosophy AI", layout="centered")
st.title("My Gemini Philosophy AI")

# --- API設定 (Secretsから読み込み) ---
if "GEMINI_API_KEY" not in st.secrets:
    st.error("SecretsにGEMINI_API_KEYを設定してください。")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# --- 思想データの読み込み ---
@st.cache_data
def load_memory():
    try:
        with open("memory.txt", "r", encoding="utf-8") as f:
            return f.read()
    except:
        return ""

philosophical_context = load_memory()

# --- モデルとチャットの初期化 ---
# 404エラーを避けるため、安定版のモデル名を指定します
if "messages" not in st.session_state:
    st.session_state.messages = []
    
if "chat" not in st.session_state:
    model = genai.GenerativeModel(
        model_name="models/gemini-1.5-flash-latest",  # ここをフルネームに修正
        system_instruction=f"あなたは私の思想の理解者です。以下を前提に対話してください：\n\n{philosophical_context}"
    )
    st.session_state.chat = model.start_chat(history=[])

# 過去の履歴を表示
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- チャット対話実行 ---
if prompt := st.chat_input("対話を開始..."):
    # ユーザー入力を表示
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Geminiの返答を生成
    with st.chat_message("assistant"):
        try:
            response = st.session_state.chat.send_message(prompt)
            answer = response.text
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
        except Exception as e:
            st.error(f"接続エラーが発生しました: {e}")
