import streamlit as st
import google.generativeai as genai
from streamlit_mic_recorder import mic_recorder

# --- 1. 網頁基礎設定 ---
st.set_page_config(page_title="暖心繪本大師", page_icon="🎨", layout="centered")

# --- 2. 安全讀取秘密金鑰 (從 Streamlit Cloud Secrets 讀取) ---
api_key = st.secrets.get("GEMINI_API_KEY")

# --- 3. UI 與動畫美化 (標準尺寸 18px + 動態指引) ---
st.markdown(f"""
    <style>
    /* 文字尺寸調回標準 (18px) */
    html, body, [class*="css"] {{ font-size: 18px !important; }}
    
    .main-title {{
        background: linear-gradient(45deg, #E67E22, #F1C40F);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 38px !important;
        font-weight: 800;
        text-align: center;
        animation: fadeIn 1.2s ease-out;
    }}
    
    /* 複製指引橫幅動畫 (呼吸效果) */
    .copy-banner {{
        background-color: #D4EFDF;
        border: 2px solid #27AE60;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        margin: 20px 0;
        animation: breath 2.5s infinite ease-in-out;
    }}
    @keyframes breath {{
        0% {{ transform: scale(1); box-shadow: 0 0 0 0 rgba(39, 174, 96, 0.4); }}
        50% {{ transform: scale(1.02); box-shadow: 0 0 15px 5px rgba(39, 174, 96, 0.2); }}
        100% {{ transform: scale(1); box-shadow: 0 0 0 0 rgba(39, 174, 96, 0.4); }}
    }}

    .step-card {{
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        border-left: 6px solid #E67E22;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        margin-bottom: 22px;
    }}

    /* 隱藏側邊欄 (當偵測到金鑰時) */
    [data-testid="stSidebar"] {{ display: {"none" if api_key else "block"}; }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. 主畫面 UI ---
st.markdown('<h1 class="main-title">暖心繪本大師</h1>', unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #7F8C8D;'>分享回憶故事，生成精美繪本製作指令</p>", unsafe_allow_html=True)

if not api_key:
    st.error("🔑 偵測不到內置金鑰。請在 Advanced settings 設定 Secrets。")
    with st.sidebar:
        api_key = st.text_input("手動輸入 API Key 進行測試：", type="password")

# --- 5. 第一步：故事錄音 ---
st.markdown('<div class="step-card"><h3>🎤 第一步：分享回憶故事</h3><p style="font-size: 16px;">按一下紅點開始說故事，講完後再按一次結束。</p></div>', unsafe_allow_html=True)

audio_record = mic_recorder(
    start_prompt="🔴 開始錄音",
    stop_prompt="⏹️ 錄音結束",
    key='recorder'
)

if 'transcript' not in st.session_state:
    st.session_state.transcript = ""

# AI 語音轉錄邏輯
if audio_record and api_key:
    with st.spinner("🧠 AI 正在傾聽並記錄您的故事..."):
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.0-flash")
            audio_data = {"mime_type": "audio/webm", "data": audio_record['bytes']}
            response = model.generate_content(["請將這段語音轉錄為繁體中文，保留原本的口氣。", audio_data])
            st.session_state.transcript = response.text
            st.toast("辨識成功！", icon="✅")
        except Exception as e:
            st.error("暫時無法辨識語音，請確認 API Key 是否正確。")

st.session_state.transcript = st.text_area("故事草稿（可在此修改內容）：", height=150, value=st.session_state.transcript)

# --- 6. 第二步：挑選畫風 ---
st.markdown('<div class="step-card"><h3>🎨 第二步：挑選繪本畫風</h3></div>', unsafe_allow_html=True)
style_options = {
    "🌱 宮崎駿療癒風": "Studio Ghibli style, watercolor, lush nature, peaceful atmosphere.",
    "🏰 迪士尼經典風": "Classic Disney animation style, expressive characters, vibrant storytelling.",
    "🌅 溫暖懷舊水彩": "Warm nostalgic watercolor painting, soft lighting, emotional textures.",
    "🖌️ 傳統東方墨彩": "Traditional ink wash painting with modern colors, elegant brushwork."
}
selected_style = st.selectbox("請選擇畫風：", list(style_options.keys()))

# --- 7. 第三步：生成指令 ---
st.markdown("---")
if st.button("✨ 生成繪本製作指令", use_container_width=True, type="primary"):
    if st.session_state.transcript and api_key:
        with st.status("🧠 AI 正在編排精美的繪本分鏡...", expanded=False) as status:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(
                    model_name="gemini-2.5-flash",
                    system_instruction=f"請根據故事製作繪本指令。畫風：{style_options[selected_style]}。包含10頁分鏡與對應文字。"
                )
                response = model.generate_content(st.session_state.transcript)
                status.update(label="✅ 編排完成！", state="complete")
                
                # 超醒目複製引導橫幅
                st.markdown("""
                    <div class="copy-banner">
                        <b style="color: #1D8348; font-size: 20px;">📋 請點擊下方區塊右上角的圖示進行複製</b><br>
                        <small>複製後即可點擊按鈕前往官網貼上製作</small>
                    </div>
                """, unsafe_allow_html=True)
                
                st.code(response.text, language="text")
                st.link_button("🚀 前往 Google 官網開始製作", "https://gemini.google.com/")
            except Exception as e:
                st.error(f"生成失敗！真實原因：{e}")
