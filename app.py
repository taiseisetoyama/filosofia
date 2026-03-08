import streamlit as st
import google.generativeai as genai
import pandas as pd
import requests
import json

# --- 1. 接続設定（Secretsから取得） ---
st.set_page_config(page_title="Mirror Mind", layout="wide")

try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    SHEET_URL = st.secrets["SPREADSHEET_URL"]
    GAS_URL = st.secrets["GAS_URL"]
    CSV_URL = SHEET_URL.split("/edit")[0] + "/export?format=csv&gid=0"
except:
    st.error("StreamlitのSecrets設定が未完了です。")
    st.stop()

# APIの初期化
genai.configure(api_key=API_KEY)

# 【最重要】404を回避する絶対的なモデル指定
MODEL_NAME = "models/gemini-1.5-flash"

# --- 2. 記憶の読み込み ---
def load_memory(user_id):
    try:
        # キャッシュを回避してスプレッドシートから最新を取得
        df = pd.read_csv(f"{CSV_URL}&cache={pd.Timestamp.now().timestamp()}")
        user_data = df[df['id'].astype(str) == str(user_id)]
        if user_data.empty:
            return "初期思想：ここから思想を深化させてください。"
        return "\n\n".join(user_data['content'].astype(str).tolist())
    except:
        return "スプレッドシート読み込み待ち..."

# --- 3. ログイン画面 ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🧠 Mirror Mind Login")
    user_input = st.text_input("IDを入力してください", type="password")
    if user_input == "a":
        st.session_state.user_id = "a"
        st.session_state.logged_in = True
        st.session_state.full_memory = load_memory("a")
        st.rerun()
    st.stop()

# --- 4. 対話エンジン ---
st.title("🧠 Mirror Mind")

# モデルのセットアップ
model = genai.GenerativeModel(
    model_name=MODEL_NAME,
    system_instruction=f"あなたはユーザーの思考の鏡です。以下の【思想アーカイブ】を全ての前提として対話してください：\n\n{st.session_state.full_memory}"
)

if "messages" not in st.session_state:
    st.session_state.messages = []

# 画面分割
col_chat, col_mem = st.columns([2, 1])

with col_chat:
    # 履歴表示
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    # 入力
    if prompt := st.chat_input("NotebookLMの成果をここへ..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        with st.chat_message("assistant"):
            try:
                # 履歴によるエラーを避けるため、直接生成
                response = model.generate_content(prompt)
                txt = response.text
                st.markdown(txt)
                st.session_state.messages.append({"role": "assistant", "content": txt})
            except Exception as e:
                st.error(f"実行エラー: {e}")

with col_mem:
    st.subheader("Archive Control")
    if st.button("✨ 刻印（保存）"):
        if len(st.session_state.messages) >= 2:
            recent = f"User: {st.session_state.messages[-2]['content']}\nAI: {st.session_state.messages[-1]['content']}"
            data = {"id": st.session_state.user_id, "category": "Evolution", "content": recent}
            try:
                requests.post(GAS_URL, data=json.dumps(data))
                st.success("スプレッドシートに刻印しました")
                # 記憶をリロード
                st.session_state.full_memory = load_memory("a")
            except:
                st.error("送信エラーが発生しました")
    
    st.divider()
    st.write(f"使用モデル: {MODEL_NAME}")
    st.write(f"現在の総記憶量: {len(st.session_state.full_memory)} 文字")
