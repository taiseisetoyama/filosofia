import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="My Philosophy AI", layout="centered")
st.title("My Gemini Philosophy AI")

# 1. APIキーの設定
if "GEMINI_API_KEY" not in st.secrets:
    st.error("SecretsにGEMINI_API_KEYを設定してください。")
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

philosophical_context = load_memory()

# 3. 利用可能なモデルを自動取得してセットアップ
if "chat" not in st.session_state:
    try:
        # 今のAPIキーで使えるモデルを全取得
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # 優先順位をつけてモデルを選択
        target_model = None
        for candidate in ["models/gemini-1.5-flash", "models/gemini-1.5-flash-latest", "models/gemini-pro"]:
            if candidate in available_models:
                target_model = candidate
                break
        
        # もし見つからなければ、リストの最初にあるやつを無理やり使う
        if not target_model:
            target_model = available_models[0]
            
        st.info(f"使用モデル: {target_model}")
        
        model = genai.GenerativeModel(
            model_name=target_model,
            system_instruction=f"あなたは私の思想の理解者です。以下を前提に対話してください：\n\n{philosophical_context}"
        )
        st.session_state.chat = model.start_chat(history=[])
        st.session_state.messages = []
    except Exception as e:
        st.error(f"モデルの取得に失敗しました。APIキーを確認してください: {e}")
        st.stop()

# 4. 履歴表示
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 5. 対話実行
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
            st.error(f"接続エラーが発生しました: {e}")
