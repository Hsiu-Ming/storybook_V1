import streamlit as st
import google.generativeai as genai
from streamlit_mic_recorder import mic_recorder

# --- 1. 網頁基礎設定 ---
st.set_page_config(page_title="暖心繪本大師", page_icon="🎨", layout="centered")

# --- 2. 安全讀取秘密金鑰與初始化 ---
api_key = st.secrets.get("GEMINI_API_KEY")

# 狀態初始化
if "transcript" not in st.session_state:
    st.session_state.transcript = ""
if "last_audio_bytes" not in st.session_state:
    st.session_state.last_audio_bytes = None
if "page_count" not in st.session_state:
    st.session_state.page_count = 10

# --- 3. UI 美化 CSS ---
sidebar_display = "none" if api_key else "block"
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=ZCOOL+XiaoWei&family=Noto+Serif+TC:wght@400;700&display=swap');

html, body, [class*="css"] {{
    font-family: 'Noto Serif TC', serif;
    font-size: 17px;
}}

.stApp {{
    background:
        radial-gradient(ellipse at 20% 10%, rgba(255, 218, 150, 0.25) 0%, transparent 50%),
        radial-gradient(ellipse at 80% 90%, rgba(255, 182, 120, 0.2) 0%, transparent 50%),
        linear-gradient(160deg, #FFF9F0 0%, #FFF3E0 50%, #FFF8F0 100%);
    min-height: 100vh;
}}

.main-title {{
    font-family: 'ZCOOL XiaoWei', serif;
    background: linear-gradient(135deg, #C0392B 0%, #E67E22 40%, #F39C12 70%, #D35400 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-size: 52px !important;
    font-weight: 900;
    text-align: center;
    letter-spacing: 6px;
    line-height: 1.2;
    margin-bottom: 4px;
    filter: drop-shadow(0 2px 8px rgba(230, 126, 34, 0.25));
    animation: fadeInDown 1s ease-out;
}}

.subtitle {{
    text-align: center;
    color: #A0826D;
    font-size: 15px;
    letter-spacing: 2px;
    margin-bottom: 30px;
    animation: fadeIn 1.5s ease-out;
}}

.deco-divider {{
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 28px 0 20px;
}}
.deco-divider::before, .deco-divider::after {{
    content: '';
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, transparent, #E67E22aa, transparent);
}}
.deco-icon {{ font-size: 20px; }}

.step-card {{
    background: rgba(255, 255, 255, 0.75);
    backdrop-filter: blur(10px);
    padding: 22px 26px;
    border-radius: 16px;
    border: 1px solid rgba(230, 126, 34, 0.2);
    border-left: 5px solid #E67E22;
    box-shadow: 0 4px 24px rgba(0,0,0,0.06);
    margin-bottom: 20px;
    animation: slideUp 0.6s ease-out;
}}

.step-card h3 {{
    color: #6E2A00;
    font-family: 'ZCOOL XiaoWei', serif;
    font-size: 20px;
    letter-spacing: 2px;
    margin: 0 0 8px 0;
}}

.step-card p {{
    color: #7D6047;
    font-size: 15px;
    margin: 0;
    line-height: 1.7;
}}

.copy-banner {{
    background: linear-gradient(135deg, #D5F5E3, #A9DFBF);
    border: 2px solid #27AE60;
    padding: 18px 24px;
    border-radius: 14px;
    text-align: center;
    margin: 24px 0 16px;
    box-shadow: 0 4px 20px rgba(39, 174, 96, 0.2);
    animation: breath 2.5s infinite ease-in-out;
}}

@keyframes breath {{
    0%   {{ transform: scale(1);     box-shadow: 0 4px 20px rgba(39,174,96,0.2); }}
    50%  {{ transform: scale(1.015); box-shadow: 0 8px 30px rgba(39,174,96,0.35); }}
    100% {{ transform: scale(1);     box-shadow: 0 4px 20px rgba(39,174,96,0.2); }}
}}

@keyframes fadeInDown {{
    from {{ opacity: 0; transform: translateY(-20px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
}}
@keyframes fadeIn {{
    from {{ opacity: 0; }}
    to   {{ opacity: 1; }}
}}
@keyframes slideUp {{
    from {{ opacity: 0; transform: translateY(16px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
}}

.stButton > button[kind="primary"] {{
    background: linear-gradient(135deg, #E67E22, #D35400) !important;
    border: none !important;
    border-radius: 12px !important;
    font-family: 'ZCOOL XiaoWei', serif !important;
    font-size: 18px !important;
    letter-spacing: 3px !important;
    padding: 14px !important;
    color: white !important;
    box-shadow: 0 4px 20px rgba(230, 126, 34, 0.4) !important;
    transition: all 0.3s ease !important;
}}

.stTextArea textarea {{
    border: 1.5px solid rgba(230, 126, 34, 0.3) !important;
    border-radius: 12px !important;
    background: rgba(255,255,255,0.85) !important;
    font-family: 'Noto Serif TC', serif !important;
    font-size: 15px !important;
    color: #4A2C00;
}}

[data-testid="stSidebar"] {{ display: {sidebar_display}; }}
</style>
""", unsafe_allow_html=True)

# --- 4. 主畫面 UI 與 API 驗證 ---
st.markdown('<h1 class="main-title">暖心繪本大師</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">✦ 分享回憶故事，生成精美繪本製作指令 ✦</p>', unsafe_allow_html=True)

if not api_key:
    st.error("🔑 偵測不到內置金鑰。請在 Streamlit Cloud → Settings → Secrets 設定 GEMINI_API_KEY。")
    with st.sidebar:
        st.markdown("### 🛠️ 測試模式")
        api_key = st.text_input("手動輸入 API Key：", type="password", placeholder="AIza...")

if api_key:
    genai.configure(api_key=api_key)

# --- 5. 第一步：故事錄音與文字潤飾 ---
st.markdown('<div class="deco-divider"><span class="deco-icon">🎤</span></div>', unsafe_allow_html=True)
st.markdown("""
<div class="step-card">
    <h3>第一步　分享回憶故事</h3>
    <p>按下紅點錄音，講述您的故事。AI 會自動為您轉錄並<b>潤飾成優美的繪本文字</b>。您也可以直接在此手動打字輸入。</p>
</div>
""", unsafe_allow_html=True)

audio_record = mic_recorder(
    start_prompt="🔴 開始錄音",
    stop_prompt="⏹️ 結束錄音",
    key="recorder"
)

# 處理錄音檔轉換 (包含自動潤飾要求)
if audio_record and api_key:
    current_audio_bytes = audio_record["bytes"]
    if current_audio_bytes != st.session_state.last_audio_bytes:
        with st.spinner("🧠 AI 正在傾聽並為您的故事注入靈魂..."):
            try:
                model = genai.GenerativeModel("gemini-2.0-flash")
                mime_type = audio_record.get("mime_type", "audio/webm")
                audio_data = {"mime_type": mime_type, "data": current_audio_bytes}
                
                # 在 Prompt 中直接要求潤飾
                prompt = "請將這段語音轉錄為繁體中文，並直接將內容潤飾成適合製作繪本的優美、流暢文字，增加畫面感與溫暖的情感。"
                response = model.generate_content([prompt, audio_data])
                
                st.session_state.transcript = response.text
                st.session_state.last_audio_bytes = current_audio_bytes
                st.toast("語音辨識與潤飾成功！", icon="✅")
            except Exception as e:
                st.error(f"⚠️ 語音辨識失敗：{e}")

# 文字草稿區塊
current_text = st.text_area(
    "故事草稿（可在此修改內容）：",
    height=180,
    value=st.session_state.transcript,
    placeholder="錄音後，您的故事將顯示在這裡... 您也可以直接打字輸入。"
)
st.session_state.transcript = current_text

# 新增：手動文字潤飾按鈕
if st.button("✨ 幫我潤飾文字", use_container_width=False):
    if not api_key:
        st.warning("⚠️ 請先輸入 API Key。")
    elif not st.session_state.transcript.strip():
        st.warning("⚠️ 請先輸入或錄製故事內容。")
    else:
        with st.spinner("✍️ 正在修飾文句，讓故事更動人..."):
            try:
                model = genai.GenerativeModel("gemini-2.0-flash")
                polish_prompt = f"請作為一位專業的繪本作家，將以下文字重新潤飾。修正錯字、語句不順的地方，將其轉化為充滿畫面感、溫暖且童趣的繪本文字，不要改變原本的故事核心：\n\n{st.session_state.transcript}"
                response = model.generate_content(polish_prompt)
                st.session_state.transcript = response.text
                st.rerun() # 刷新頁面以顯示潤飾後的文字
            except Exception as e:
                st.error(f"⚠️ 潤飾失敗：{e}")

# --- 6. 第二步：挑選畫風與頁數設定 ---
st.markdown('<div class="deco-divider"><span class="deco-icon">🎨</span></div>', unsafe_allow_html=True)
st.markdown("""
<div class="step-card">
    <h3>第二步　風格與頁數設定</h3>
    <p>挑選最契合的畫風，並設定您的繪本長度。如果您不確定，可以請 AI 幫您建議最適當的頁數。</p>
</div>
""", unsafe_allow_html=True)

# 擴充後的畫風選項
style_options = {
    "🌱 宮崎駿療癒風": "Studio Ghibli style, watercolor, lush nature, peaceful atmosphere, soft light.",
    "🧸 皮克斯 3D 風": "3D render, Pixar style, cute characters, highly detailed, vivid colors, warm lighting.",
    "🖍️ 兒童粉彩蠟筆": "Children's book illustration, oil pastel, crayon texture, whimsical, vibrant, childlike charm.",
    "🏰 迪士尼經典風": "Classic Disney animation style, expressive characters, vibrant storytelling, cinematic.",
    "🌅 溫暖懷舊水彩": "Warm nostalgic watercolor painting, soft golden lighting, emotional textures, vintage feel.",
    "🎨 現代極簡插畫": "Modern flat vector illustration, minimalist, soft pastel palette, clean lines, cozy aesthetic.",
    "🖌️ 傳統東方墨彩": "Traditional ink wash painting with modern colors, elegant brushwork, poetic composition."
}

selected_style = st.selectbox("請選擇畫風：", list(style_options.keys()))

# 頁數設定與 AI 建議
col1, col2 = st.columns([3, 1])
with col1:
    page_count = st.slider("請設定繪本頁數：", min_value=4, max_value=24, value=st.session_state.page_count, step=1)
    st.session_state.page_count = page_count
with col2:
    st.write("") # 調整垂直對齊用
    st.write("")
    if st.button("💡 AI 建議頁數", use_container_width=True):
        if not st.session_state.transcript.strip():
            st.toast("請先輸入故事內容！", icon="⚠️")
        else:
            with st.spinner("計算中..."):
                try:
                    model = genai.GenerativeModel("gemini-2.0-flash")
                    # 提示 AI 只回傳數字
                    page_prompt = f"根據以下故事的長度和情節豐富度，建議適合的繪本分鏡頁數。請只回傳一個 4 到 24 之間的阿拉伯數字，不要包含任何其他文字：\n\n{st.session_state.transcript}"
                    response = model.generate_content(page_prompt)
                    suggested_pages = int(response.text.strip())
                    st.session_state.page_count = suggested_pages
                    st.rerun() # 更新滑桿數值
                except Exception as e:
                    st.toast("無法分析頁數，請手動調整", icon="⚠️")


# --- 7. 第三步：生成指令 ---
st.markdown('<div class="deco-divider"><span class="deco-icon">✨</span></div>', unsafe_allow_html=True)

if st.button("✨ 生成繪本製作指令", use_container_width=True, type="primary"):
    if not api_key:
        st.warning("⚠️ 請先輸入 API Key。")
    elif not st.session_state.transcript.strip():
        st.warning("⚠️ 請先錄音或在草稿欄輸入故事內容。")
    else:
        with st.status("🧠 AI 正在編排精美的繪本分鏡...", expanded=True) as status:
            try:
                model = genai.GenerativeModel(
                    model_name="gemini-2.0-flash", 
                    system_instruction=(
                        "你是一位專業繪本編輯。請根據使用者的故事，製作一份完整的繪本製作指令。\n"
                        f"畫風要求：{style_options[selected_style]}\n"
                        f"格式要求：共 {st.session_state.page_count} 頁分鏡，每頁包含：\n"
                        "1. 頁面編號\n2. 畫面構圖描述（英文，供 AI 繪圖使用，必須符合畫風要求）\n3. 繁體中文故事文字（2-3 句）\n"
                        "請用清晰的條列格式輸出。"
                    )
                )
                response = model.generate_content(st.session_state.transcript)
                status.update(label="✅ 編排完成！", state="complete", expanded=False)

                st.markdown("""
                    <div class="copy-banner">
                        <b style="color: #1D8348; font-size: 19px;">📋 點擊下方區塊右上角的複製圖示</b><br>
                        <small style="color: #555;">複製後前往官網貼上，即可開始製作您的繪本</small>
                    </div>
                """, unsafe_allow_html=True)

                st.code(response.text, language="text")

                st.link_button(
                    "🚀 前往 Google AI Studio 開始製作",
                    "https://aistudio.google.com/",
                    use_container_width=True
                )

            except Exception as e:
                st.error(f"⚠️ 生成失敗：{e}")
