import streamlit as st
import google.generativeai as genai

# アプリの設定
st.set_page_config(page_title="My Philosophy AI", layout="centered")
st.title("My Gemini Philosophy AI")

# 1. APIキーの確認
if "GEMINI_API_KEY" not in st.secrets:
    st.error("StreamlitのSecretsにGEMINI_API_KEYが設定されていません。")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# 2. 思想データの読み込み（memory.txt）
@st.cache_data
def load_memory():
    try:
        with open("memory.txt", "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return "" # ファイルがない場合は空にする

philosophical_context = load_memory()

# 3. モデルの初期化
# モデル名を "models/gemini-1.5-pro" に戻し、より安定した書き方にします
model = genai.GenerativeModel(
    model_name="models/gemini-1.5-pro",
    system_instruction=f"あなたは私の思想の理解者です。以下の背景を前提に、制限を恐れず深く対話してください：\n\n{philosophical_context}",
    safety_settings=[
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]
)

# 4. 会話の管理
if "messages" not in st.session_state:
    st.session_state.messages = []
    # チャットセッションの開始（system_instructionをモデル初期化時に渡す形式に変更）
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
            response = st.session_state.chat.send_message(prompt, stream=True)
            full_text = ""
            placeholder = st.empty()
            for chunk in response:
                if chunk.text:
                    full_text += chunk.text
                    placeholder.markdown(full_text + "▌")
            placeholder.markdown(full_text)
            st.session_state.messages.append({"role": "assistant", "content": full_text})
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")
            st.info("APIキーが正しいか、Google AI Studioで制限がかかっていないか確認してください。")
