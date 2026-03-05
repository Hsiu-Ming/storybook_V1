import streamlit as st
from google import genai
from google.genai import types
from streamlit_mic_recorder import mic_recorder
import time

# --- 1. 網頁基礎設定 ---
st.set_page_config(page_title="暖心繪本大師", page_icon="🎨", layout="centered")

# --- 2. 安全讀取秘密金鑰與狀態初始化 ---
api_key = st.secrets.get("GEMINI_API_KEY")

if "transcript" not in st.session_state:
    st.session_state.transcript = ""
if "last_audio_bytes" not in st.session_state:
    st.session_state.last_audio_bytes = None
if "page_count" not in st.session_state:
    st.session_state.page_count = 10
if "app_step" not in st.session_state:
    st.session_state.app_step = 1

# 初始化最新的 Gemini 客戶端
client = None
if api_key:
    client = genai.Client(api_key=api_key)

# --- 3. UI 美化 CSS (升級 3D 魔法城門特效 & 修復圖示) ---
sidebar_display = "none" if api_key else "block"
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;700&display=swap');

/* 👇 正確的字體設定，解決缺字問題，同時保護系統圖示不變亂碼 */
html, body, [class*="css"], .stApp {{ 
    font-family: 'Noto Sans TC', 'Taipei Sans TC Beta', sans-serif !important; 
    font-size: 18px; 
    letter-spacing: 0.5px; 
}}

/* 確保 Streamlit 內建圖示（打勾、箭頭）維持原始字體 */
.material-symbols-rounded, .material-icons, [data-testid="stIconMaterial"] {{
    font-family: 'Material Symbols Rounded', 'Material Icons' !important;
}}

.stApp {{ background: radial-gradient(ellipse at 20% 10%, rgba(255, 218, 150, 0.25) 0%, transparent 50%), radial-gradient(ellipse at 80% 90%, rgba(255, 182, 120, 0.2) 0%, transparent 50%), linear-gradient(160deg, #FFF9F0 0%, #FFF3E0 50%, #FFF8F0 100%); min-height: 100vh; }}
.main-title {{ font-weight: 700; background: linear-gradient(135deg, #C0392B 0%, #E67E22 40%, #F39C12 70%, #D35400 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; font-size: 48px !important; text-align: center; letter-spacing: 4px; margin-bottom: 8px; }}

.custom-progress-bg {{ background-color: #E5E7E9; border-radius: 20px; height: 28px; width: 100%; margin: 20px 0 30px 0; box-shadow: inset 0 2px 5px rgba(0,0,0,0.1); overflow: hidden; }}
.custom-progress-bar {{ background: linear-gradient(90deg, #F1C40F, #F39C12, #D35400); height: 100%; border-radius: 20px; display: flex; align-items: center; justify-content: center; color: white; font-weight: 700; font-size: 14px; transition: width 0.8s cubic-bezier(0.25, 0.8, 0.25, 1); }}

/* 🌟 全新特效：魔法城門展開 (結合模糊、發光、放大落下) */
@keyframes magicalGateOpen {{
    0% {{ opacity: 0; transform: translateY(-30px) scale(0.9); filter: blur(8px) brightness(0.5); }}
    50% {{ opacity: 0.8; transform: translateY(10px) scale(1.02); filter: blur(2px) brightness(1.1); box-shadow: 0 15px 40px rgba(230, 126, 34, 0.4); }}
    100% {{ opacity: 1; transform: translateY(0) scale(1); filter: blur(0) brightness(1); box-shadow: 0 10px 30px rgba(230, 126, 34, 0.2); }}
}}

/* 🔓 已解鎖的彩色卡片 (明亮展開) */
.unlocked-card {{ 
    background: rgba(255, 255, 255, 0.95); 
    padding: 24px 30px; 
    border-radius: 20px; 
    border: 3px solid #F39C12; 
    border-top: 12px solid #F39C12; /* 加厚頂部增加大門感 */
    margin-bottom: 24px; 
    animation: magicalGateOpen 0.9s cubic-bezier(0.2, 0.8, 0.2, 1) both; 
}}

/* 🔒 未解鎖的灰階卡片 (厚重緊閉的城門) */
.locked-card {{ 
    background: linear-gradient(180deg, #EAECEE 0%, #D5D8DC 100%); 
    padding: 20px 30px; 
    border-radius: 20px; 
    border: 3px solid #ABB2B9; 
    border-top: 12px solid #808B96; /* 沉重的鐵門感 */
    margin-bottom: 24px; 
    color: #7F8C8D; 
    opacity: 0.7; 
    box-shadow: inset 0 5px 15px rgba(0,0,0,0.05);
    transition: all 0.5s ease; 
}}
.locked-card h3 {{ color: #7F8C8D !important; }}
.unlocked-card h3 {{ color: #D35400; font-weight: 700; font-size: 26px; margin: 0 0 12px 0; }}
.unlocked-card p {{ color: #5C4033; font-size: 18px; line-height: 1.8; }}

/* 闖關按鈕特效：加入呼吸燈光暈引導 */
@keyframes buttonPulse {{
    0% {{ box-shadow: 0 4px 10px rgba(211, 84, 0, 0.15); }}
    50% {{ box-shadow: 0 4px 25px rgba(211, 84, 0, 0.4); }}
    100% {{ box-shadow: 0 4px 10px rgba(211, 84, 0, 0.15); }}
}}

.next-step-btn > button {{ 
    background: white !important; 
    color: #D35400 !important; 
    border: 3px solid #D35400 !important; 
    border-radius: 16px !important; 
    font-weight: 700 !important; 
    font-size: 20px !important; 
    padding: 12px 24px !important; 
    animation: buttonPulse 2.5s infinite ease-in-out;
    transition: all 0.3s ease !important; 
}}
.next-step-btn > button:hover {{ 
    background: #FFF3E0 !important; 
    transform: translateY(-4px) scale(1.03); 
    box-shadow: 0 10px 20px rgba(211, 84, 0, 0.3) !important; 
}}

.stButton > button[kind="primary"] {{ background: linear-gradient(135deg, #27AE60, #2ECC71) !important; border: none !important; border-radius: 16px !important; font-weight: 700 !important; font-size: 22px !important; padding: 18px !important; color: white !important; box-shadow: 0 6px 20px rgba(39, 174, 96, 0.4) !important; }}
[data-testid="stSidebar"] {{ display: {sidebar_display}; }}
</style>
""", unsafe_allow_html=True)

# --- 4. 主畫面 UI ---
st.markdown('<h1 class="main-title">暖心繪本大師</h1>', unsafe_allow_html=True)

if not api_key:
    st.error("🔑 偵測不到內置金鑰。")
    with st.sidebar:
        api_key = st.text_input("手動輸入 API Key：", type="password")
        if api_key:
            client = genai.Client(api_key=api_key)

progress_percentage = int((st.session_state.app_step / 3) * 100)
st.markdown(f"""
<div class="custom-progress-bg">
    <div class="custom-progress-bar" style="width: {progress_percentage}%;">
        ⭐ 當前進度：第 {st.session_state.app_step} / 3 關
    </div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 🚩 第一關：分享故事
# ==========================================
st.markdown("""
<div class="unlocked-card">
    <h3>🎯 第一關：說出您的故事</h3>
    <p>按下方的<b>紅點</b>開始錄音，就像在跟孫子聊天一樣。說完後再按一次結束，AI 會幫您把語氣變得更優美！</p>
</div>
""", unsafe_allow_html=True)

audio_record = mic_recorder(start_prompt="🔴 點這裡開始錄音", stop_prompt="⏹️ 點這裡結束錄音", key="recorder")

if audio_record and client:
    current_audio_bytes = audio_record["bytes"]
    if current_audio_bytes != st.session_state.last_audio_bytes:
        with st.spinner("🧠 正在專心聽您說故事..."):
            try:
                mime_type = audio_record.get("mime_type", "audio/webm")
                audio_part = types.Part.from_bytes(data=current_audio_bytes, mime_type=mime_type)
                prompt = "請將這段語音轉錄為繁體中文，並直接將內容潤飾成適合製作繪本的優美、流暢文字，增加畫面感與溫暖的情感。"
                
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[prompt, audio_part]
                )
                
                st.session_state.transcript = response.text
                st.session_state.last_audio_bytes = current_audio_bytes
                st.toast("🎉 故事記錄成功！", icon="✅")
            except Exception as e:
                st.error(f"⚠️ 錄音處理失敗：{e}")

st.session_state.transcript = st.text_area(
    "📝 您的故事內容（可以在這裡修改）：",
    height=150,
    value=st.session_state.transcript,
    placeholder="錄音完成後，文字會出現在這裡..."
)

col_btn1, col_btn2 = st.columns([1, 1])
with col_btn1:
    if st.button("✨ 幫我把文字修得更漂亮", use_container_width=True):
        if st.session_state.transcript.strip() and client:
            with st.spinner("✍️ 正在修飾文句..."):
                try:
                    polish_prompt = f"請將以下文字重新潤飾。修正錯字、語句不順，轉化為溫暖、充滿畫面感的繪本文字：\n\n{st.session_state.transcript}"
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=polish_prompt
                    )
                    st.session_state.transcript = response.text
                    st.toast("✨ 文字變得更優美了！", icon="🪄")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"⚠️ 潤飾失敗：{e}")
        else:
            st.warning("請先輸入故事喔！")

with col_btn2:
    st.markdown('<div class="next-step-btn">', unsafe_allow_html=True)
    if st.button("✅ 故事完成了，開啟下一關 ➔", use_container_width=True):
        if st.session_state.transcript.strip():
            if st.session_state.app_step < 2:
                st.toast("🎉 城門已開啟！解鎖畫風選擇！", icon="🔓")
                time.sleep(1.2)
            st.session_state.app_step = max(st.session_state.app_step, 2)
            st.rerun()
        else:
            st.warning("請先說一段故事喔！")
    st.markdown('</div>', unsafe_allow_html=True)

st.write("---")

# ==========================================
# 🚩 第二關：挑選畫風與頁數
# ==========================================
if st.session_state.app_step < 2:
    st.markdown('<div class="locked-card"><h3>🔒 第二關：重重城門尚未解鎖</h3><p>完成上方的故事分享，就能推開這扇大門！</p></div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="unlocked-card"><h3>🎯 第二關：為故事穿上美麗的外衣</h3><p>來挑選您最喜歡的繪畫風格吧！</p></div>', unsafe_allow_html=True)

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
                    page_prompt = f"根據故事長度建議繪本頁數，只回傳4到24之間的數字：\n\n{st.session_state.transcript}"
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=page_prompt
                    )
                    st.session_state.page_count = int(response.text.strip())
                    st.rerun()
                except:
                    st.toast("無法分析，請手動調整", icon="⚠️")
    
    st.markdown('<div class="next-step-btn">', unsafe_allow_html=True)
    if st.button("✅ 設定好了，推開最終大門 ➔", use_container_width=True):
        if st.session_state.app_step < 3:
            st.toast("🎉 通往終點的城門已展開！", icon="🔓")
            time.sleep(1.2)
        st.session_state.app_step = 3
        st.session_state.selected_style = selected_style
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.write("---")

# ==========================================
# 🚩 第三關：生成指令 (純中文全自動連載版)
# ==========================================
if st.session_state.app_step < 3:
    if st.session_state.app_step > 1:
        st.markdown('<div class="locked-card"><h3>🔒 最終關：神秘的魔法陣</h3><p>設定好您的畫風後，就能啟動這座魔法陣囉！</p></div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="unlocked-card" style="border-color: #27AE60; border-top-color: #27AE60;"><h3 style="color: #27AE60;">👑 最終關：見證魔法時刻</h3><p>請點擊下方綠色大按鈕，產生適合貼給 Gemini Gem 的純中文連載腳本！</p></div>', unsafe_allow_html=True)

    if st.button("🌟 施展魔法！生成純中文繪本腳本", use_container_width=True, type="primary"):
        with st.status("🧠 AI 正在為您編排純中文的分鏡腳本...", expanded=True) as status:
            try:
                # 移除下拉選單字串中的 Emoji，只保留畫風純文字 (例如從 "🌱 宮崎駿療癒風" 變成 "宮崎駿療癒風")
                style_zh = selected_style.split(" ", 1)[1] if " " in selected_style else selected_style
                
                sys_instruct = (
                    "你是一位專業的繪本編輯。請根據使用者的故事，製作一份純繁體中文的 Markdown 繪本分鏡腳本。\n\n"
                    f"**畫風設定**: {style_zh}\n"
                    f"**總頁數**: {st.session_state.page_count}\n\n"
                    "【請嚴格按照以下格式輸出，請直接開始輸出分鏡腳本內容，絕對不要包含任何開頭的問候語或引導對話，並且「絕對不要使用任何表情符號 (Emoji)」】：\n\n"
                    "## 第 1 頁\n"
                    "**畫面描述**: [請用繁體中文詳細描述畫面構圖、人物長相、動作、背景與光影。請在句尾加上「畫風：(帶入畫風設定)」以確保風格一致]\n"
                    "**故事內文**: [2-3 句繁體中文故事文字，充滿溫度與畫面感]\n"
                    "---\n"
                    "（後續頁數以此類推，直到最後一頁）"
                )
                
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=st.session_state.transcript,
                    config=types.GenerateContentConfig(
                        system_instruction=sys_instruct
                    )
                )
                status.update(label="✅ 繪本腳本編排完成！", state="complete", expanded=False)
                
                st.balloons() 
                st.success("📋 請點擊右上角圖示複製下方的全中文腳本，直接前往您的 Gemini Gem 貼上並送出！")
                
                st.code(response.text, language="markdown")

                st.link_button(
                    "🚀 前往專屬 Gemini Gem (Storybook) 開始製作",
                    "https://gemini.google.com/gem/storybook",
                    use_container_width=True
                )

            except Exception as e:
                st.error(f"⚠️ 生成失敗：{e}")
