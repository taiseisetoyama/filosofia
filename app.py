import streamlit as st
import google.generativeai as genai

# --- 1. ページ基本設定 ---
st.set_page_config(page_title="Deep Mind Evolution", layout="centered")
st.title("My Recursive Philosophy AI")

# --- 2. API設定 ---
if "GEMINI_API_KEY" not in st.secrets:
    st.error("SecretsにGEMINI_API_KEYを設定してください。")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# --- 3. モデルの自動判別（1.5 Flashを最優先して回数制限を回避） ---
@st.cache_resource
def get_stable_model():
    try:
        # 使えるモデルをリストアップ
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # 1日1500回枠の 1.5-flash を最優先で探す
        priority = [
            "models/gemini-1.5-flash",
            "models/gemini-1.5-flash-latest",
            "models/gemini-2.0-flash",
            "models/gemini-2.5-flash" # 2.5は1日20回制限のため最後に
        ]
        
        for name in priority:
            if name in available_models:
                return name
        return available_models[0]
    except:
        # 万が一リスト取得に失敗した場合の保険
        return "models/gemini-1.5-flash"

MODEL_NAME = get_stable_model()

# --- 4. ブラウザ上の記憶（Session State）の初期化 ---
if "philosophy_base" not in st.session_state:
    try:
        with open("memory.txt", "r", encoding="utf-8") as f:
            st.session_state.philosophy_base = f.read()
    except:
        st.session_state.philosophy_base = "初期状態：対話を通じて思想を構築します。"

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 5. 思想の統合（再エンコード）関数 ---
def evolve_philosophy(current_base, recent_messages):
    chat_log = "\n".join([f"{m
