import streamlit as st
import google.generativeai as genai

# --- 1. ページ基本設定 ---
st.set_page_config(page_title="Philosophy AI", layout="centered")
st.title("My Gemini Philosophy AI")

# --- 2. API設定と思想データの読み込み ---
if "GEMINI_API_KEY" not in st.secrets:
    st.error("StreamlitのSecretsにGEMINI_API_KEYを設定してください。")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

@st.cache_data
def load_memory():
    try:
        with open("memory.txt", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "思想データ（memory.txt）が見つかりません。"

philosophical_context = load_memory()

# --- 3. モデルの定義 ---
# 安全設定（Safety Settings）を解除して、自由な対話を可能にします
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",  # 応答速度と安定性重視
    system_instruction=f"あなたは私の思想の理解者です。以下の思想を背景に対話してください：\n\n{philosophical_context}",
    safety_settings=[
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]
)

# --- 4. チャット履歴の初期化 ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    # 通信を発生させずに履歴を初期化
    st.session_state.chat = model.start_chat(history=[])

# 過去の会話を表示
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 5. 対話の実行 ---
if prompt := st.chat_input("思考の続きを..."):
    # ユーザー入力を表示・保存
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Geminiからの返答を生成
    with st.chat_message("assistant"):
        try:
            # ストリーミング表示でライブ感を出す
            response = st.session_state.chat.send_message(prompt, stream=True)
            full_text = ""
            placeholder = st.empty()
            for chunk in response:
                if chunk.text:
                    full_text += chunk.text
                    placeholder.markdown(full_text + "▌")
            placeholder.markdown(full_text)
            
            # 返答を履歴に保存
            st.session_state.messages.append({"role": "assistant", "content": full_text})
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")
