import streamlit as st
import google.generativeai as genai
import pandas as pd
import requests
import json

# --- 設定 ---
st.set_page_config(page_title="Mirror Mind", layout="wide")
st.title("🧠 Mirror Mind")

# Secretsの読み込み
API_KEY = st.secrets["GEMINI_API_KEY"]
SHEET_URL = st.secrets["SPREADSHEET_URL"]
GAS_URL = st.secrets["GAS_URL"]
# スプレッドシートをCSVとして読み込むためのURL変換
CSV_URL = SHEET_URL.split("/edit")[0] + "/export?format=csv&gid=0"

genai.configure(api_key=API_KEY)

# 【修正ポイント】モデル名をより汎用的な書き方に変更
MODEL_NAME = "gemini-1.5-flash" 

# --- 記憶の読み込み関数 ---
def load_memory(user_id):
    try:
        # スプレッドシートからデータを取得
        df = pd.read_csv(CSV_URL)
        # ID列が数値として扱われる場合があるため文字列に変換して比較
        user_data = df[df['id'].astype(str) == str(user_id)]
        
        if user_data.empty:
            # 記憶が空なら memory.txt を探す
            try:
                with open("memory.txt", "r", encoding="utf-8") as f:
                    return f.read()
            except:
                return "初期思想：ここから対話を開始します。"
        
        # 保存されている内容を結合
        return "\n\n".join(user_data['content'].astype(str).tolist())
    except Exception as e:
        return f"記憶の読み込み中にエラーが発生しました（スプレッドシートが空の可能性があります）"

# --- ログインセッション ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    user_input = st.text_input("IDを入力してください", type="password")
    if user_input == "a":
        st.session_state.user_id = "a"
        st.session_state.logged_in = True
        with st.spinner("膨大な記憶を同期中..."):
            st.session_state.full_memory = load_memory("a")
        st.rerun()
    st.stop()

# --- AI構築 ---
# 5万文字の記憶をシステム命令として叩き込む
model = genai.GenerativeModel(
    model_name=MODEL_NAME,
    system_instruction=f"あなたはユーザーの思想そのものです。以下の【過去の膨大な記憶】を前提に、矛盾のない、深みのある対話を行ってください。：\n\n{st.session_state.full_memory}"
)

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 画面表示 ---
col1, col2 = st.columns([2, 1])

with col1:
    # 履歴の表示
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    # 入力フォーム
    if prompt := st.chat_input("思考を深化させる..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            try:
                # エラーが起きやすい chat.send_message ではなく generate_content を使用
                # 過去の会話の流れも数件含める
                context_messages = st.session_state.messages[-6:] 
                response = model.generate_content(prompt)
                
                if response.text:
                    st.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                else:
                    st.error("AIからの返答が空でした。")
            except Exception as e:
                st.error(f"接続エラーが発生しました: {e}")

with col2:
    st.subheader("Memory Archive")
    if st.button("✨ 今の対話を刻印"):
        if len(st.session_state.messages) >= 2:
            # 直近の1往復を保存
            recent_log = f"User: {st.session_state.messages[-2]['content']}\nAI: {st.session_state.messages[-1]['content']}"
            data = {
                "id": st.session_state.user_id,
                "category": "Evolution",
                "content": recent_log
            }
            try:
                res = requests.post(GAS_URL, data=json.dumps(data))
                if res.status_code == 200:
                    st.success("スプレッドシートに刻印しました")
                else:
                    st.error(f"同期失敗: {res.status_code}")
            except Exception as e:
                st.error(f"通信エラー: {e}")
        else:
            st.warning("刻印する会話がまだありません")

    st.divider()
    st.write("📖 現在の記憶量:", len(st.session_state.full_memory), "文字")
    with st.expander("アーカイブの断片を確認"):
        st.text(st.session_state.full_memory[:500] + "...")
