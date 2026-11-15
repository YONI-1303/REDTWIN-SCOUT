import streamlit as st

def apply_redtwin_visual_theme():
    st.markdown(r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');

:root {
  --rt-bg: #080A12;
  --rt-surface: #101426;
  --rt-panel: rgba(19,24,45,.82);
  --rt-violet: #9275FF;
  --rt-lavender: #BDAEFF;
  --rt-cyan: #55C9D9;
  --rt-text: #F2F2FA;
  --rt-muted: #A4A9BD;
  --rt-border: rgba(180,174,255,.15);
}

html, body, [class*="css"] {
  font-family: 'Manrope', 'Segoe UI', sans-serif;
}

.stApp {
  background:
    radial-gradient(ellipse at 12% 0%, rgba(105,76,190,.20), transparent 40%),
    radial-gradient(ellipse at 92% 28%, rgba(48,116,151,.12), transparent 35%),
    linear-gradient(145deg,#080A12,#0B1020 55%,#090B16) !important;
  color: var(--rt-text);
  isolation: isolate;
}

.stApp:before {
  content: "";
  position: fixed;
  inset: 0;
  z-index: -1;
  pointer-events: none;
  background-image:
    linear-gradient(rgba(180,174,255,.025) 1px, transparent 1px),
    linear-gradient(90deg,rgba(180,174,255,.025) 1px, transparent 1px);
  background-size: 54px 54px;
  mask-image: linear-gradient(to bottom,black,transparent 88%);
}

[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="stMainBlockContainer"] {
  background: transparent !important;
}

[data-testid="stMainBlockContainer"] {
  max-width: 1550px;
  padding-top: 2.2rem;
  padding-bottom: 4rem;
}

[data-testid="stHeader"] {
  background: rgba(8,10,18,.65) !important;
  backdrop-filter: blur(18px);
}

[data-testid="stSidebar"] {
  background: rgba(9,11,23,.94) !important;
  border-right: 1px solid var(--rt-border);
  backdrop-filter: blur(24px);
}

[data-testid="stSidebar"] > div:first-child {
  background: transparent !important;
}

[data-testid="stSidebar"] * {
  color: var(--rt-text);
}

.brand {
  display: flex;
  align-items: center;
  gap: 13px;
  color: #F5F2FF !important;
  font-size: 1.13rem !important;
  font-weight: 800 !important;
  letter-spacing: .13em;
  padding: 12px 3px 22px;
}

.brand:before {
  content: "";
  display: inline-block;
  flex: 0 0 37px;
  width: 37px;
  height: 37px;
  border: 1px solid rgba(189,174,255,.8);
  border-radius: 50%;
  background:
    radial-gradient(circle at 68% 30%,#F4EEFF 0 3%,transparent 5%),
    radial-gradient(circle at 37% 40%,#BDAEFF 0 9%,#9275FF 24%,transparent 27%),
    radial-gradient(circle at 45% 45%,rgba(85,201,217,.65),transparent 65%);
  box-shadow: 0 0 25px rgba(146,117,255,.28), inset 0 0 14px rgba(189,174,255,.22);
}

h1, h2, h3 {
  color: #F5F3FF !important;
  letter-spacing: -.045em !important;
  font-weight: 750 !important;
}

h1 { font-size: clamp(2rem,4vw,3.2rem) !important; }
h2 { font-size: 1.75rem !important; }
h3 { font-size: 1.24rem !important; }

p, .stMarkdown, label {
  color: #D4D7E8;
}

[data-testid="stCaptionContainer"] {
  color: var(--rt-muted) !important;
}

[data-testid="stMetric"] {
  background: linear-gradient(145deg,rgba(27,31,57,.94),rgba(15,19,36,.92)) !important;
  border: 1px solid var(--rt-border) !important;
  border-radius: 16px !important;
  padding: 19px 21px !important;
  box-shadow: 0 12px 34px rgba(0,0,0,.13);
  transition: transform .2s ease,border-color .2s ease,box-shadow .2s ease;
}

[data-testid="stMetric"]:hover {
  transform: translateY(-3px);
  border-color: rgba(189,174,255,.4) !important;
  box-shadow: 0 15px 38px rgba(75,48,150,.17);
}

[data-testid="stMetricLabel"] {
  color: #AEB2C9 !important;
  font-size: .78rem !important;
  letter-spacing: .07em;
  text-transform: uppercase;
}

[data-testid="stMetricValue"] {
  color: #F4F0FF !important;
  font-family: 'DM Mono', monospace !important;
}

.stButton > button,
.stDownloadButton > button {
  border: 1px solid rgba(189,174,255,.35) !important;
  border-radius: 10px !important;
  background: linear-gradient(120deg,#7254CE,#8D70EE) !important;
  color: white !important;
  font-weight: 650 !important;
  transition: all .2s ease !important;
  box-shadow: 0 5px 20px rgba(105,76,190,.18);
}

.stButton > button:hover,
.stDownloadButton > button:hover {
  transform: translateY(-2px);
  border-color: #C5B8FF !important;
  box-shadow: 0 9px 26px rgba(146,117,255,.3);
}

[data-baseweb="select"] > div,
[data-baseweb="input"] > div,
.stTextInput input,
.stTextArea textarea {
  background: #12172A !important;
  color: #F2F0FF !important;
  border-color: rgba(189,174,255,.2) !important;
  border-radius: 10px !important;
}

[data-baseweb="popover"],
[data-baseweb="menu"] {
  background: #171B31 !important;
  border: 1px solid var(--rt-border) !important;
}

[data-testid="stSidebar"] [role="radiogroup"] label {
  border-radius: 9px;
  padding: 9px 11px;
  transition: background .18s ease;
}

[data-testid="stSidebar"] [role="radiogroup"] label:hover {
  background: rgba(146,117,255,.13);
}

[data-testid="stPlotlyChart"] {
  border: 1px solid var(--rt-border);
  border-radius: 15px;
  background: rgba(13,17,33,.45);
  padding: 5px;
}

[data-testid="stDataFrame"],
[data-testid="stTable"] {
  border: 1px solid var(--rt-border);
  border-radius: 13px;
  overflow: hidden;
}

[data-testid="stTabs"] button {
  color: #AEB2C9 !important;
  font-weight: 600;
}

[data-testid="stTabs"] button[aria-selected="true"] {
  color: #C7B8FF !important;
  border-bottom-color: var(--rt-violet) !important;
}

[data-testid="stAlert"] {
  border-radius: 12px;
  border: 1px solid var(--rt-border);
  background: rgba(20,24,45,.8);
}

hr {
  border-color: rgba(189,174,255,.14) !important;
}

code, .mono {
  font-family: 'DM Mono', monospace !important;
  color: #C8BAFF !important;
}

::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: #090B16; }
::-webkit-scrollbar-thumb {
  background: #39315C;
  border-radius: 10px;
}
::-webkit-scrollbar-thumb:hover { background: #9275FF; }

footer { visibility: hidden; }

@media (max-width: 768px) {
  [data-testid="stMainBlockContainer"] {
    padding: 1.1rem .9rem 2rem;
  }
  h1 { font-size: 2rem !important; }
}
@media (prefers-reduced-motion: reduce) {
  *, *:before, *:after {
    animation-duration: .01ms !important;
    transition-duration: .01ms !important;
  }
}
</style>
""", unsafe_allow_html=True)
