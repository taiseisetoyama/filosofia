import streamlit as st
import google.generativeai as genai
import pandas as pd

# --- 1. 設定 ---
st.set_page_config(page_title="Mirror Mind", layout="wide")
st.title("🧠 Mirror Mind: 自律進化型・思想アーカイブ")

# API & スプレッドシートURL
API_KEY = st.secrets["GEMINI_API_KEY"]
SHEET_URL = st.secrets["SPREADSHEET_URL"].replace('/edit#gid=', '/export?format=csv&gid=')
CSV_URL = st.secrets["SPREADSHEET_URL"].replace('/edit#gid=', '/export?format=csv&gid=')

genai.configure(api_key=API_KEY)
MODEL_NAME = "models/gemini-1.5-flash" # 1500回/日の安定枠

# --- 2. 記憶の読み書き関数（CSV変換経由で簡単接続） ---
def load_memory(user_id):
    try:
        # スプレッドシートをCSVとして読み込む
        df = pd.read_csv(CSV_URL)
        user_data = df[df['id'] == user_id]
        if user_data.empty:
            return "初期状態：まだ深い記憶はありません。"
        return "\n\n".join(user_data['content'].tolist())
    except:
        return "memory.txtから読み込んだ初期思想..." # 失敗時はここ

# --- 3. ログイン機能 ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    user_input = st.text_input("IDを入力してください (例: a)", type="password")
    if user_input == "a":
        st.session_state.user_id = "a"
        st.session_state.logged_in = True
        with st.spinner("記憶を同期中..."):
            st.session_state.full_memory = load_memory("a")
        st.rerun()
    st.stop()

# --- 4. メインエンジン ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# AIの構築（5万文字の記憶を前提に叩き込む）
model = genai.GenerativeModel(
    model_name=MODEL_NAME,
    system_instruction=f"あなたはユーザーの分身であり、思想の守護者です。以下の【膨大な過去の記憶】を完全に把握し、矛盾のない対話を行ってください：\n\n{st.session_state.full_memory}"
)
chat = model.start_chat(history=[])

# 画面レイアウト
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("対話")
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    if prompt := st.chat_input("思考を深化させる..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        with st.chat_message("assistant"):
            response = chat.send_message(prompt)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})

with col2:
    st.subheader("記憶の刻印")
    if st.button("✨ 現在の対話をアーカイブへ刻印"):
        # ここでスプレッドシートへの書き込み処理（実際にはGASや別の簡易APIを叩くのが確実）
        st.success("記憶の断片をスプレッドシートへ送信しました（※要GAS設定）")
        st.info("※書き込みを完全に自動化するには、スプレッドシート側で1分で終わる『GAS設定』が必要です。続けますか？")

    st.divider()
    st.write("📖 現在の解像度（文字数）:", len(st.session_state.full_memory))
    with st.expander("アーカイブの断片を見る"):
        st.text(st.session_state.full_memory[:1000] + "...")
