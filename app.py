import streamlit as st
import google.generativeai as genai
from streamlit_mic_recorder import mic_recorder

# --- 1. 網頁基礎設定 ---
st.set_page_config(page_title="暖心繪本大師", page_icon="🎨", layout="centered")

# --- 2. 安全讀取秘密金鑰與狀態初始化 ---
api_key = st.secrets.get("GEMINI_API_KEY")

# 初始化所有的 Session State
if "transcript" not in st.session_state:
    st.session_state.transcript = ""
if "last_audio_bytes" not in st.session_state:
    st.session_state.last_audio_bytes = None
if "page_count" not in st.session_state:
    st.session_state.page_count = 10
# 新增：紀錄目前進行到第幾關 (預設第 1 關)
if "app_step" not in st.session_state:
    st.session_state.app_step = 1

# --- 3. UI 美化 CSS (台北黑體 & 闖關風格) ---
sidebar_display = "none" if api_key else "block"
st.markdown(f"""
<style>
/* 引入思源黑體作為台北黑體的安全備案 */
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;700&display=swap');

html, body, [class*="css"] {{
    /* 優先使用台北黑體，若無則使用思源黑體 */
    font-family: 'Taipei Sans TC Beta', 'Taipei Sans TC', 'Noto Sans TC', 'Microsoft JhengHei', sans-serif;
    font-size: 18px;
    letter-spacing: 0.5px;
}}

.stApp {{
    background:
        radial-gradient(ellipse at 20% 10%, rgba(255, 218, 150, 0.25) 0%, transparent 50%),
        radial-gradient(ellipse at 80% 90%, rgba(255, 182, 120, 0.2) 0%, transparent 50%),
        linear-gradient(160deg, #FFF9F0 0%, #FFF3E0 50%, #FFF8F0 100%);
    min-height: 100vh;
}}

.main-title {{
    font-weight: 700;
    background: linear-gradient(135deg, #C0392B 0%, #E67E22 40%, #F39C12 70%, #D35400 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-size: 48px !important;
    text-align: center;
    letter-spacing: 4px;
    line-height: 1.3;
    margin-bottom: 8px;
    filter: drop-shadow(0 2px 4px rgba(230, 126, 34, 0.2));
}}

.subtitle {{
    text-align: center;
    color: #8C6239;
    font-size: 18px;
    font-weight: 400;
    letter-spacing: 2px;
    margin-bottom: 30px;
}}

/* 關卡卡片設計：增加對比度與圓角，保護長輩眼睛 */
.step-card {{
    background: rgba(255, 255, 255, 0.9);
    padding: 24px 30px;
    border-radius: 20px;
    border: 2px solid #F39C12;
    box-shadow: 0 8px 24px rgba(230, 126, 34, 0.15);
    margin-bottom: 24px;
}}

.step-card h3 {{
    color: #D35400;
    font-weight: 700;
    font-size: 24px;
    margin: 0 0 12px 0;
    display: flex;
    align-items: center;
    gap: 10px;
}}

.step-card p {{
    color: #5C4033;
    font-weight: 400;
    font-size: 17px;
    line-height: 1.8;
    margin: 0;
}}

/* 下一步按鈕的特殊設計 */
.next-step-btn > button {{
    background: white !important;
    color: #D35400 !important;
    border: 2px solid #D35400 !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    font-size: 18px !important;
    padding: 10px 24px !important;
    transition: all 0.3s ease !important;
}}
.next-step-btn > button:hover {{
    background: #FFF3E0 !important;
    transform: translateY(-2px);
}}

.stButton > button[kind="primary"] {{
    background: linear-gradient(135deg, #E67E22, #D35400) !important;
    border: none !important;
    border-radius: 16px !important;
    font-weight: 700 !important;
    font-size: 20px !important;
    letter-spacing: 2px !important;
    padding: 16px !important;
    color: white !important;
    box-shadow: 0 6px 20px rgba(230, 126, 34, 0.4) !important;
}}

.stTextArea textarea {{
    border: 2px solid #F5CBA7 !important;
    border-radius: 12px !important;
    font-size: 18px !important;
    line-height: 1.6 !important;
    color: #3E2723;
}}

[data-testid="stSidebar"] {{ display: {sidebar_display}; }}
</style>
""", unsafe_allow_html=True)

# --- 4. 主畫面 UI 與 API 驗證 ---
st.markdown('<h1 class="main-title">暖心繪本大師</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">✦ 用您的聲音，留下最珍貴的回憶 ✦</p>', unsafe_allow_html=True)

if not api_key:
    st.error("🔑 偵測不到內置金鑰。")
    with st.sidebar:
        api_key = st.text_input("手動輸入 API Key：", type="password")

if api_key:
    genai.configure(api_key=api_key)

# ==========================================
# 🚩 關卡一：分享故事
# ==========================================
st.markdown("""
<div class="step-card">
    <h3>🎯 第一關：說出您的故事</h3>
    <p>請按下方的<b>紅點按鈕</b>開始錄音，就像在跟孫子聊天一樣輕鬆。說完後再按一次結束，AI 會幫您把語氣變得更優美喔！您也可以直接在框框內打字。</p>
</div>
""", unsafe_allow_html=True)

audio_record = mic_recorder(
    start_prompt="🔴 點這裡開始錄音",
    stop_prompt="⏹️ 點這裡結束錄音",
    key="recorder"
)

# 處理錄音與潤飾
if audio_record and api_key:
    current_audio_bytes = audio_record["bytes"]
    if current_audio_bytes != st.session_state.last_audio_bytes:
        with st.spinner("🧠 正在專心聽您說故事，並轉成優美的文字..."):
            try:
                model = genai.GenerativeModel("gemini-2.0-flash")
                mime_type = audio_record.get("mime_type", "audio/webm")
                audio_data = {"mime_type": mime_type, "data": current_audio_bytes}
                prompt = "請將這段語音轉錄為繁體中文，並直接將內容潤飾成適合製作繪本的優美、流暢文字，增加畫面感與溫暖的情感。"
                response = model.generate_content([prompt, audio_data])
                
                st.session_state.transcript = response.text
                st.session_state.last_audio_bytes = current_audio_bytes
                st.toast("故事記錄成功！", icon="✅")
            except Exception as e:
                st.error("⚠️ 錄音處理失敗，請稍後再試。")

# 文字草稿區塊
current_text = st.text_area(
    "📝 您的故事內容（可以在這裡修改）：",
    height=180,
    value=st.session_state.transcript,
    placeholder="錄音完成後，文字會出現在這裡..."
)
st.session_state.transcript = current_text

col_btn1, col_btn2 = st.columns([1, 1])
with col_btn1:
    if st.button("✨ 幫我把文字修得更漂亮", use_container_width=True):
        if st.session_state.transcript.strip():
            with st.spinner("✍️ 正在修飾文句..."):
                try:
                    model = genai.GenerativeModel("gemini-2.0-flash")
                    polish_prompt = f"請將以下文字重新潤飾。修正錯字、語句不順，轉化為溫暖、充滿畫面感的繪本文字：\n\n{st.session_state.transcript}"
                    response = model.generate_content(polish_prompt)
                    st.session_state.transcript = response.text
                    st.rerun()
                except:
                    st.error("⚠️ 潤飾失敗")
        else:
            st.warning("請先輸入故事喔！")

with col_btn2:
    # 推進到第二關的按鈕
    st.markdown('<div class="next-step-btn">', unsafe_allow_html=True)
    if st.button("✅ 故事準備好了，進入下一步 ➔", use_container_width=True):
        if st.session_state.transcript.strip():
            st.session_state.app_step = max(st.session_state.app_step, 2)
            st.rerun()
        else:
            st.warning("請先說一段故事，或輸入文字喔！")
    st.markdown('</div>', unsafe_allow_html=True)

st.write("---")

# ==========================================
# 🚩 關卡二：挑選畫風與頁數 (需解鎖)
# ==========================================
if st.session_state.app_step >= 2:
    st.markdown("""
    <div class="step-card">
        <h3>🎯 第二關：選擇繪本的模樣</h3>
        <p>故事有了，現在為它挑選一件美麗的外衣吧！您喜歡哪一種繪畫風格呢？</p>
    </div>
    """, unsafe_allow_html=True)

    style_options = {
        "🌱 宮崎駿療癒風": "Studio Ghibli style, watercolor, lush nature, peaceful atmosphere, soft light.",
        "🧸 皮克斯 3D 風": "3D render, Pixar style, cute characters, highly detailed, vivid colors, warm lighting.",
        "🖍️ 兒童粉彩蠟筆": "Children's book illustration, oil pastel, crayon texture, whimsical, vibrant, childlike charm.",
        "🌅 溫暖懷舊水彩": "Warm nostalgic watercolor painting, soft golden lighting, emotional textures, vintage feel.",
        "🖌️ 傳統東方墨彩": "Traditional ink wash painting with modern colors, elegant brushwork, poetic composition."
    }

    selected_style = st.selectbox("🎨 請挑選您喜歡的畫風：", list(style_options.keys()))

    st.write("📖 **設定繪本長度**")
    col1, col2 = st.columns([3, 1])
    with col1:
        page_count = st.slider("想要幾頁的繪本呢？", min_value=4, max_value=24, value=st.session_state.page_count, step=1)
        st.session_state.page_count = page_count
    with col2:
        st.write("")
        st.write("")
        if st.button("💡 請 AI 幫我建議", use_container_width=True):
            with st.spinner("計算中..."):
                try:
                    model = genai.GenerativeModel("gemini-2.0-flash")
                    page_prompt = f"根據故事長度建議繪本頁數，只回傳4到24之間的數字：\n\n{st.session_state.transcript}"
                    response = model.generate_content(page_prompt)
                    st.session_state.page_count = int(response.text.strip())
                    st.rerun()
                except:
                    st.toast("無法分析，請手動調整", icon="⚠️")
    
    # 推進到第三關的按鈕
    st.markdown('<div class="next-step-btn">', unsafe_allow_html=True)
    if st.button("✅ 設定好了，準備製作繪本 ➔", use_container_width=True):
        st.session_state.app_step = 3
        st.session_state.selected_style = selected_style # 記住選擇的畫風
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.write("---")

# ==========================================
# 🚩 關卡三：生成指令 (需解鎖)
# ==========================================
if st.session_state.app_step >= 3:
    st.markdown("""
    <div class="step-card" style="border-color: #27AE60;">
        <h3 style="color: #27AE60;">🎯 最後一步：見證魔法時刻</h3>
        <p>太棒了！一切準備就緒。請點擊下方的大按鈕，AI 就會幫您把故事變成完整的繪本分鏡腳本。</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🌟 施展魔法！生成繪本製作指令", use_container_width=True, type="primary"):
        with st.status("🧠 AI 正在為您編排精美的分鏡...", expanded=True) as status:
            try:
                # 取得剛剛記住的畫風
                style_en = style_options[st.session_state.get("selected_style", list(style_options.keys())[0])]
                
                model = genai.GenerativeModel(
                    model_name="gemini-2.0-flash", 
                    system_instruction=(
                        "你是一位專業繪本編輯。請根據使用者的故事，製作一份完整的繪本製作指令。\n"
                        f"畫風要求：{style_en}\n"
                        f"格式要求：共 {st.session_state.page_count} 頁分鏡，每頁包含：\n"
                        "1. 頁面編號\n2. 畫面構圖描述（英文，供 AI 繪圖使用）\n3. 繁體中文故事文字（2-3 句）\n"
                        "請用清晰的條列格式輸出。"
                    )
                )
                response = model.generate_content(st.session_state.transcript)
                status.update(label="✅ 繪本指令編排完成！", state="complete", expanded=False)
                st.balloons() # 達成任務的彩蛋慶祝效果！

                st.success("📋 請點擊下方區塊右上角的圖示複製文字，然後前往 Google AI Studio 貼上即可開始製作！")
                st.code(response.text, language="text")

                st.link_button(
                    "🚀 前往 Google AI Studio 開始製作",
                    "https://aistudio.google.com/",
                    use_container_width=True
                )

            except Exception as e:
                st.error(f"⚠️ 生成失敗，請檢查網路或金鑰狀態。")
