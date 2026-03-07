import streamlit as st
import google.generativeai as genai
import pandas as pd
import requests
import json

# --- 1. 基本設定 ---
st.set_page_config(page_title="Mirror Mind", layout="wide")
st.title("🧠 Mirror Mind: 思想アーカイブ")

# Secretsからの読み込み
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    SHEET_URL = st.secrets["SPREADSHEET_URL"]
    GAS_URL = st.secrets["GAS_URL"]
    # CSV取得用URLに変換
    CSV_URL = SHEET_URL.split("/edit")[0] + "/export?format=csv&gid=0"
except Exception as e:
    st.error("Secretsの設定が不足しています。")
    st.stop()

# API設定（最新の安定した呼び出し方）
genai.configure(api_key=API_KEY)
# 404を避けるための最も安定したモデル名
MODEL_NAME = "gemini-1.5-flash-latest"

# --- 2. 記憶の同期エンジン ---
def load_memory(user_id):
    try:
        # スプレッドシートを読み込む（キャッシュを無効化して常に最新を）
        df = pd.read_csv(f"{CSV_URL}&cache={pd.Timestamp.now().timestamp()}")
        user_data = df[df['id'].astype(str) == str(user_id)]
        
        if user_data.empty:
            # 記憶が空なら memory.txt を探す
            try:
                with open("memory.txt", "r", encoding="utf-8") as f:
                    return f.read()
            except:
                return "初期思想：ここから対話を開始し、思想を深化させてください。"
        
        # 過去の全内容を結合
        return "\n\n".join(user_data['content'].astype(str).tolist())
    except:
        return "データベース接続中...（またはスプレッドシートが空です）"

# --- 3. シンプルログイン ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    user_input = st.text_input("IDを入力", type="password")
    if user_input == "a":
        st.session_state.user_id = "a"
        st.session_state.logged_in = True
        with st.spinner("思想を同期中..."):
            st.session_state.full_memory = load_memory("a")
        st.rerun()
    st.stop()

# --- 4. 対話エンジン ---
# 5万文字を想定したシステムプロンプト
model = genai.GenerativeModel(
    model_name=MODEL_NAME,
    system_instruction=f"あなたはユーザーの思考の鏡です。以下の【膨大な思想アーカイブ】をすべての対話の前提としてください。：\n\n{st.session_state.full_memory}"
)

if "messages" not in st.session_state:
    st.session_state.messages = []

# レイアウト構成
col_chat, col_mem = st.columns([2, 1])

with col_chat:
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("NotebookLMでまとめた思想をここへ..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        with st.chat_message("assistant"):
            try:
                # 履歴を含めず、常に「全記憶＋最新の問い」で生成（安定重視）
                response = model.generate_content(prompt)
                if response.text:
                    st.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"エラー: {e}")

with col_mem:
    st.subheader("Memory Core")
    if st.button("✨ この対話をアーカイブへ刻印"):
        if len(st.session_state.messages) >= 2:
            # 直近のやり取りを抽出
            recent_log = f"User: {st.session_state.messages[-2]['content']}\nAI: {st.session_state.messages[-1]['content']}"
            data = {"id": st.session_state.user_id, "category": "Evolution", "content": recent_log}
            try:
                res = requests.post(GAS_URL, data=json.dumps(data))
                if res.status_code == 200:
                    st.success("スプレッドシートへ同期完了")
                    # 刻印後、メモリを再読み込みして最新化
                    st.session_state.full_memory = load_memory("a")
                else:
                    st.error(f"同期失敗: {res.status_code}")
            except Exception as e:
                st.error(f"通信エラー: {e}")
        else:
            st.warning("刻印する内容がありません")

    st.divider()
    st.write("📖 現在の総文字数:", len(st.session_state.full_memory))
    with st.expander("アーカイブの断片"):
        st.text(st.session_state.full_memory[:1000] + "...")
