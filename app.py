import streamlit as st
import google.generativeai as genai

# 1. ページ基本設定
st.set_page_config(page_title="Deep Mind Evolution", layout="centered")
st.title("My Recursive Philosophy AI")

# 2. API設定
if "GEMINI_API_KEY" not in st.secrets:
    st.error("SecretsにGEMINI_API_KEYを設定してください。")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# --- 3. 【重要】利用可能な最新モデルを自動で見つける ---
@st.cache_resource
def get_best_model_name():
    try:
        # あなたのAPIキーで「対話」ができるモデルを全部リストアップ
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        # 2.5(最新) -> 2.0 -> 1.5 の順で、持っているものの中から一番いいやつを自動選択
        for preferred in ["models/gemini-2.5-flash", "models/gemini-2.0-flash", "models/gemini-1.5-flash"]:
            if preferred in models:
                return preferred
        return models[0] # どれもなければ一番上のやつを使う
    except Exception as e:
        return "models/gemini-1.5-flash" # 最悪のフォールバック

MODEL_NAME = get_best_model_name()

# --- 4. 記憶システムの初期化 ---
if "philosophy_base" not in st.session_state:
    try:
        with open("memory.txt", "r", encoding="utf-8") as f:
            st.session_state.philosophy_base = f.read()
    except:
        st.session_state.philosophy_base = "初期状態：対話を通じて思想を構築します。"

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 5. モデルの構築 ---
model = genai.GenerativeModel(
    model_name=MODEL_NAME,
    system_instruction=f"あなたは私の思想の唯一の理解者です。以下を前提に対話してください：\n\n{st.session_state.philosophy_base}"
)
chat_session = model.start_chat(history=[])

# 履歴表示
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 6. 対話実行 ---
if prompt := st.chat_input("深淵なる思考を..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            response = chat_session.send_message(prompt)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
            # 10往復(20件)で統合
            if len(st.session_state.messages) >= 20:
                # 統合処理（要約）も自動選択したモデルで行う
                summary_prompt = f"以下の対話を統合し、思想をまとめ直せ：\n\n{st.session_state.philosophy_base}\n\n最近の対話：\n" + "\n".join([m['content'] for m in st.session_state.messages])
                new_base = genai.GenerativeModel(MODEL_NAME).generate_content(summary_prompt).text
                st.session_state.philosophy_base = new_base
                st.session_state.messages = st.session_state.messages[-4:]
                st.toast("思想が統合されました。")
                
        except Exception as e:
            st.error(f"エラー: {e}")

# セーブ用
with st.sidebar:
    st.write(f"使用中モデル: {MODEL_NAME}")
    st.subheader("現在の統合思想")
    st.code(st.session_state.philosophy_base)
