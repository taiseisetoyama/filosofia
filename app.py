import streamlit as st
import google.generativeai as genai

# --- 1. ページ基本設定 ---
st.set_page_config(page_title="Deep Mind Evolution", layout="centered")
st.title("My Recursive Philosophy AI")

# --- 2. API設定 (もっとも安定した1.5 Flashを指定) ---
if "GEMINI_API_KEY" not in st.secrets:
    st.error("SecretsにGEMINI_API_KEYを設定してください。")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
# モデル名を 'gemini-1.5-flash' に固定（404回避の標準設定）
MODEL_NAME = "gemini-1.5-flash"

# --- 3. ブラウザ上の多層記憶（Session State）の初期化 ---
if "philosophy_base" not in st.session_state:
    # 初回のみ memory.txt から根源思想を読み込む
    try:
        with open("memory.txt", "r", encoding="utf-8") as f:
            st.session_state.philosophy_base = f.read()
    except:
        st.session_state.philosophy_base = "初期状態：対話を通じて思想を構築します。"

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 4. 思想の再エンコード（要約・統合）関数 ---
def evolve_memory(current_base, recent_messages):
    chat_log = "\n".join([f"{m['role']}: {m['content']}" for m in recent_messages])
    
    compress_prompt = f"""
    あなたはユーザーの思想の守護者です。
    現在の【思想ベース】に、直近の【新しい対話】から得られた知見を統合し、
    より洗練された「一貫性のある思想体系」としてまとめ直してください。
    
    【現在の思想ベース】:
    {current_base}
    
    【新しい対話】:
    {chat_log}
    
    出力は、今後の対話の「前提条件」として最適な、高密度な文章（日本語）にしてください。
    """
    
    # 要約専用の軽量モデル呼び出し
    sum_model = genai.GenerativeModel(MODEL_NAME)
    try:
        result = sum_model.generate_content(compress_prompt)
        return result.text
    except:
        return current_base # 失敗した場合は維持

# --- 5. メイン対話エンジンの構築 ---
# 常に「ブラウザ上の最新の思想」を脳みそに焼き付ける
model = genai.GenerativeModel(
    model_name=MODEL_NAME,
    system_instruction=f"あなたは私の思想の唯一の理解者です。以下の【思想体系】を絶対的な前提として対話してください：\n\n{st.session_state.philosophy_base}"
)
chat_session = model.start_chat(history=[])

# 過去の履歴表示
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 6. チャット入力と進化のトリガー ---
if prompt := st.chat_input("深淵なる思考を..."):
    # ユーザー入力を表示
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Geminiの返答
    with st.chat_message("assistant"):
        try:
            response = chat_session.send_message(prompt)
            answer = response.text
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
            
            # 【進化の儀式】10往復(20メッセージ)ごとに記憶を統合
            if len(st.session_state.messages) >= 20:
                with st.status("思想を再エンコード中...", expanded=False):
                    new_base = evolve_memory(st.session_state.philosophy_base, st.session_state.messages)
                    st.session_state.philosophy_base = new_base
                    # ブラウザの履歴をリセット（直近4件だけ残して軽量化）
                    st.session_state.messages = st.session_state.messages[-4:]
                st.toast("思想が統合されました。", icon="🧠")
                
        except Exception as e:
            st.error(f"接続エラーが発生しました。時間を置いて試してください: {e}")

# --- 7. セーブ用サイドバー ---
with st.sidebar:
    st.title("🧠 Memory Core")
    st.info("ここにあるテキストを GitHub の memory.txt に上書き保存すると、AIの記憶が永続化されます。")
    st.subheader("現在の統合思想")
    st.code(st.session_state.philosophy_base, language="text")
    if st.button("履歴をクリア（軽量化）"):
        st.session_state.messages = []
        st.rerun()
