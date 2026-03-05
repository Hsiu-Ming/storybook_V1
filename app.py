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

.stButton > button[kind="primary"] {{ background: linear-gradient(135deg, #2
