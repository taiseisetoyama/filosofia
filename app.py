import streamlit as st
import google.generativeai as genai

# --- 1. ページ基本設定 ---
st.set_page_config(page_title="Deep Mind Evolution", layout="centered")
st.title("My Recursive Philosophy AI")

# --- 2. API設定（Secretsから読み込み） ---
if "GEMINI_API_KEY" not in st.secrets:
    st.error("StreamlitのSecretsにGEMINI_API_KEYを設定してください。")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# --- 3. ブラウザ上の多層記憶（Session State）の初期化 ---
if "philosophy_base" not in st.session_state:
    # 初回起動時のみ memory.txt（初期思想）を読み込む
    try:
        with open("memory.txt", "r", encoding="utf-8") as f:
            st.session_state.philosophy_base = f.read()
    except:
        st.session_state.philosophy_base = "【初期状態】対話を通じて思想を構築します。"

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 4. 記憶の「再構築・統合」関数 ---
def re_encode_philosophy(current_base, recent_messages):
    context = "\n".join([f"{m['role']}: {m['content']}" for m in recent_messages])
    
    compress_prompt = f"""
    あなたはユーザーの思想の守護者です。
    現在の【思想ベース】に、直近の【新しい対話】から得られた知見を統合し、
    より洗練された「一貫性のある思想体系」としてまとめ直してください。
    
    【現在の思想ベース】:
    {current_base}
    
    【新しい対話】:
    {context}
    
    出力は、今後の対話の「前提条件」として最適な、高密度な文章にしてください。
    不要な挨拶やメタな説明は省き、思想の核だけを抽出してください。
    """
    
    # 統合処理には速くて制限の緩い 1.5 Flash を使用
    model = genai.GenerativeModel("gemini-1.5-flash")
    result = model.generate_content(compress_prompt)
    return result.text

# --- 5. モデルの構築（1.5 Flashを直接指名） ---
# これにより1日20回制限を回避し、1日1500回まで対話可能になります
model = genai.GenerativeModel(
    model_name="models/gemini-1.5-flash",
    system_instruction=f"あなたは私の思想の唯一の理解者です。以下の【進化し続ける思想体系】を絶対的な前提として対話してください：\n\n{st.session_state.philosophy_base}"
)
chat = model.start_chat(history=[])

# 履歴表示
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 6. 対話実行 ---
if prompt := st.chat_input("思考を深化させる..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            response = chat.send_message(prompt)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
            # 10往復（20メッセージ）ごとにブラウザ内の記憶を統合
            if len(st.session_state.messages) >= 20:
                with st.spinner("思想を再エンコード中..."):
                    new_base = re_encode_philosophy(st.session_state.philosophy_base, st.session_state.messages)
                    st.session_state.philosophy_base = new_base
                    # ブラウザの履歴をリセット（直近4件だけ残して軽量化）
                    st.session_state.messages = st.session_state.messages[-4:]
                    st.success("思想が統合され、AIの解像度が上がりました。")
        except Exception as e:
            st.error(f"接続エラーが発生しました。時間を置いて試してください: {e}")

# --- 7. スマホ用セーブ機能（サイドバーと拡張表示） ---
st.divider()
with st.expander("💾 現在の思想（ここをコピーしてGitHubのmemory.txtへ）"):
    st.info("これが今、AIが認識している最新の思想です。永続化したい場合はGitHubに保存してください。")
    st.code(st.session_state.philosophy_base)

with st.sidebar:
    st.subheader
