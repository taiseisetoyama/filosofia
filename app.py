import streamlit as st
import google.generativeai as genai
import pandas as pd
import requests
import json

# --- 1. 基本設定 ---
st.set_page_config(page_title="Mirror Mind", layout="wide")
st.title("🧠 Mirror Mind")

try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    SHEET_URL = st.secrets["SPREADSHEET_URL"]
    GAS_URL = st.secrets["GAS_URL"]
    CSV_URL = SHEET_URL.split("/edit")[0] + "/export?format=csv&gid=0"
except Exception as e:
    st.error("Secretsの設定（API_KEY, SHEET_URL, GAS_URL）を確認してください。")
    st.stop()

genai.configure(api_key=API_KEY)

# --- 2. 確実に動くモデルを自動選定 ---
@st.cache_resource
def get_working_model():
    try:
        # 今のAPIキーで使えるモデルを全取得
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # 優先順位をつけて、存在するものを採用する
        targets = ["models/gemini-1.5-flash", "models/gemini-1.5-flash-latest", "models/gemini-pro"]
        for t in targets:
            if t in available_models:
                return t
        return available_models[0] # 見つかった中から何でもいいから動くやつを返す
    except Exception as e:
        # 最悪のフォールバック
        return "models/gemini-1.5-flash"

MODEL_NAME = get_working_model()

# --- 3. 記憶エンジン ---
def load_memory(user_id):
    try:
        # キャッシュを回避して最新を取得
        df = pd.read_csv(f"{CSV_URL}&cache={pd.Timestamp.now().timestamp()}")
        user_data = df[df['id'].astype(str) == str(user_id)]
        if user_data.empty:
            try:
                with open("memory.txt", "r", encoding="utf-8") as f: return f.read()
            except: return "初期思想：ここから対話を開始します。"
        return "\n\n".join(user_data['content'].astype(str).tolist())
    except:
        return "スプレッドシートの1行目に id, category, content, date と入力してください。"

# --- 4. ログイン ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    user_input = st.text_input("ID", type="password")
    if user_input == "a":
        st.session_state.user_id = "a"
        st.session_state.logged_in = True
        st.session_state.full_memory = load_memory("a")
        st.rerun()
    st.stop()

# --- 5. 対話 ---
model = genai.GenerativeModel(
    model_name=MODEL_NAME,
    system_instruction=f"あなたはユーザーの思考の鏡です。以下を前提としてください：\n\n{st.session_state.full_memory}"
)

if "messages" not in st.session_state:
    st.session_state.messages = []

col_chat, col_mem = st.columns([2, 1])

with col_chat:
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("NotebookLMの成果をここへ..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        with st.chat_message("assistant"):
            try:
                response = model.generate_content(prompt)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")

with col_mem:
    st.subheader("Archive Control")
    if st.button("✨ 刻印（スプレッドシートへ保存）"):
        if len(st.session_state.messages) >= 2:
            recent_log = f"User: {st.session_state.messages[-2]['content']}\nAI: {st.session_state.messages[-1]['content']}"
            data = {"id": st.session_state.user_id, "category": "Evolution", "content": recent_log}
            try:
                requests.post(GAS_URL, data=json.dumps(data))
                st.success("記憶を同期しました")
                st.session_state.full_memory = load_memory("a")
            except:
                st.error("送信エラー")
        else:
            st.warning("刻印する会話がありません")
    
    st.divider()
    st.write(f"使用モデル: {MODEL_NAME}")
    st.write("現在の記憶量:", len(st.session_state.full_memory), "文字")
