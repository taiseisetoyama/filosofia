import streamlit as st
import google.generativeai as genai
import pandas as pd
import requests
import json

# --- 1. 基本設定 ---
st.set_page_config(page_title="Mirror Mind", layout="wide")

try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    SHEET_URL = st.secrets["SPREADSHEET_URL"]
    GAS_URL = st.secrets["GAS_URL"]
    CSV_URL = SHEET_URL.split("/edit")[0] + "/export?format=csv&gid=0"
except:
    st.error("Secretsの設定（API_KEY, SHEET_URL, GAS_URL）を再確認してください。")
    st.stop()

# APIの初期化
genai.configure(api_key=API_KEY)

# 【最重要：最新モデル 2.0 Flash を直接指定】
# 回数制限（1日20回）はありますが、最新のため 404 エラーは起きません。
MODEL_NAME = "gemini-2.0-flash"

# --- 2. 記憶の読み込み ---
def load_memory(user_id):
    try:
        # スプレッドシートから最新を取得
        df = pd.read_csv(f"{CSV_URL}&cache={pd.Timestamp.now().timestamp()}")
        user_data = df[df['id'].astype(str) == str(user_id)]
        if user_data.empty: return "初期思想から開始します。"
        return "\n\n".join(user_data['content'].astype(str).tolist())
    except:
        return "スプレッドシートの見出し(id, category, content, date)を確認してください。"

# --- 3. ログイン ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🧠 Mirror Mind Login")
    user_input = st.text_input("IDを入力 (a)", type="password")
    if user_input == "a":
        st.session_state.user_id = "a"
        st.session_state.logged_in = True
        st.session_state.full_memory = load_memory("a")
        st.rerun()
    st.stop()

# --- 4. 対話 ---
st.title("🧠 Mirror Mind")

# モデルのセットアップ
model = genai.GenerativeModel(model_name=MODEL_NAME)

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
                # 記憶をプロンプトに結合して送信
                full_prompt = f"以下の思想アーカイブを背景として対話してください。\n\n【思想アーカイブ】\n{st.session_state.full_memory}\n\n【問い】\n{prompt}"
                response = model.generate_content(full_prompt)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                # ここで回数制限（429）が出た場合は、その旨を表示
                st.error(f"エラー: {e}")

with col_mem:
    st.subheader("Control")
    if st.button("✨ 刻印"):
        if len(st.session_state.messages) >= 2:
            recent = f"User: {st.session_state.messages[-2]['content']}\nAI: {st.session_state.messages[-1]['content']}"
            data = {"id": st.session_state.user_id, "category": "Evolution", "content": recent}
            requests.post(GAS_URL, data=json.dumps(data))
            st.success("刻印完了")
            st.session_state.full_memory = load_memory("a")
    
    st.divider()
    st.write(f"稼働モデル: {MODEL_NAME}")
    st.write(f"現在の記憶量: {len(st.session_state.full_memory)} 文字")
