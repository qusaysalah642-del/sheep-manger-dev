import streamlit as st
import pandas as pd
import json
import os
import uuid
import ast
from datetime import datetime

# ─── إعداد الصفحة ────────────────────────────────────────────────────────────
st.set_page_config(page_title="Sheep Manager Pro", page_icon="🐑", layout="wide")

# تهيئة رسائل الإشعار لتبدو واضحة بعد إعادة التشغيل (Rerun)
if "success_msg" not in st.session_state:
    st.session_state.success_msg = None

# نظام الألوان والخطوط (Design tokens)
C_BG_DEEP = "#0b1f16"        
C_BG_PANEL = "#123326"       
C_BG_PANEL_2 = "#16402f"     
C_BORDER = "rgba(255,255,255,0.08)"
C_TEXT = "#eef6f0"
C_TEXT_MUTED = "#93b3a1"
C_GREEN = "#4c9a6a"          
C_GREEN_DARK = "#2f6b48"
C_AMBER = "#d3a15c"          
C_AMBER_DARK = "#a97c3c"
C_DANGER = "#e2665a"

if not os.path.exists("images"): os.makedirs("images")
if "toast" not in st.session_state: st.session_state.toast = None

if st.session_state.toast:
    st.toast(st.session_state.toast)
    st.session_state.toast = None

st.markdown(f"""
<style>  
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@600;700;800&family=Tajawal:wght@400;500;700&display=swap');  
  
    html, body, [class*="css"] {{ font-family: 'Tajawal', sans-serif; direction: rtl; text-align: right; }}  
    h1, h2, h3, .app-hero-title {{ font-family: 'Cairo', sans-serif; }}  
  
    .stApp {{ background: linear-gradient(180deg, {C_BG_DEEP} 0%, #0e2a1e 100%); color: {C_TEXT}; }}  
  
    /* ─── الهيدر الرئيسي ─── */  
    .app-hero {{  
        display: flex; align-items: center; gap: 18px;  
        background: linear-gradient(135deg, {C_BG_PANEL} 0%, {C_BG_DEEP} 100%);  
        border: 1px solid {C_BORDER};  
        border-radius: 18px;  
        padding: 22px 28px;  
        margin-bottom: 22px;  
        box-shadow: 0 6px 24px rgba(0,0,0,0.25);  
    }}  
    .app-hero-icon {{  
        font-size: 40px; line-height: 1;  
        background: linear-gradient(135deg, {C_AMBER}, {C_AMBER_DARK});  
        width: 64px; height: 64px; border-radius: 16px;  
        display: flex; align-items: center; justify-content: center;  
        flex-shrink: 0;  
        box-shadow: 0 4px 14px rgba(211,161,92,0.25);  
    }}  
    .app-hero-title {{ font-size: 26px; font-weight: 800; margin: 0; color: {C_TEXT}; }}  
    .app-hero-subtitle {{ font-size: 14px; color: {C_TEXT_MUTED}; margin-top: 2px; }}  
  
    /* ─── تبويبات علوية ─── */  
    .stTabs [data-baseweb="tab-list"] {{ gap: 6px; background: transparent; justify-content: center; }}  
    .stTabs [data-baseweb="tab"] {{  
        background: {C_BG_PANEL};  
        border: 1px solid {C_BORDER};  
        border-radius: 999px !important;  
        padding: 8px 20px;  
        color: {C_TEXT_MUTED};  
        font-weight: 700;  
    }}  
    .stTabs [aria-selected="true"] {{  
        background: linear-gradient(135deg, {C_GREEN} 0%, {C_GREEN_DARK} 100%) !important;  
        color: white !important;  
        border: 1px solid {C_GREEN} !important;  
    }}  
  
    /* ─── البطاقات ─── */  
    [data-testid="stExpander"] {{  
        background: {C_BG_PANEL};  
        border: 1px solid {C_BORDER} !important;  
        border-radius: 14px !important;  
        margin-bottom: 10px;  
    }}  
    [data-testid="stVerticalBlockBorderWrapper"] {{ border-radius: 14px !important; }}  
  
    /* ─── الأزرار ─── */  
    .stButton > button {{  
        background: linear-gradient(135deg, {C_GREEN} 0%, {C_GREEN_DARK} 100%);  
        color: white; border: none; border-radius: 10px; width: 100%;  
        font-weight: 700; padding: 10px 0;  
    }}  
    .stButton > button:hover {{ filter: brightness(1.12); }}  
    .stButton > button[kind="primary"] {{ background: linear-gradient(135deg, {C_DANGER} 0%, #b8443a 100%); }}  
    .stFormSubmitButton > button {{  
        background: linear-gradient(135deg, {C_AMBER} 0%, {C_AMBER_DARK} 100%) !important;  
        color: #24170a !important; border: none; border-radius: 10px; font-weight: 800;  
    }}  
  
    /* ─── الحقول ─── */  
    .stTextInput input, .stNumberInput input, .stDateInput input, .stSelectbox div[data-baseweb="select"] > div {{  
        background: {C_BG_DEEP} !important; border: 1px solid {C_BORDER} !important;  
        border-radius: 10px !important; color: {C_TEXT} !important;  
    }}  
  
    /* ─── شارات ─── */  
    .ear-tag {{  
        display: inline-flex; align-items: center; gap: 8px;  
        background: linear-gradient(135deg, {C_AMBER} 0%, {C_AMBER_DARK} 100%);  
        color: #24170a; font-weight: 800; font-size: 13px;  
        padding: 5px 14px 5px 10px; border-radius: 4px 14px 14px 4px; margin: 2px 4px 2px 0;  
    }}  
    .ear-tag::before {{  
        content: ''; width: 7px; height: 7px; border-radius: 50%;  
        background: {C_BG_DEEP}; border: 2px solid rgba(0,0,0,0.2); flex-shrink: 0;  
    }}  
    .info-chip {{  
        display: inline-flex; align-items: center; gap: 6px;  
        background: rgba(255,255,255,0.05); border: 1px solid {C_BORDER};  
        color: {C_TEXT}; padding: 4px 12px; border-radius: 999px; font-size: 13px; margin: 2px 4px 2px 0;  
    }}  
</style>  
""", unsafe_allow_html=True)

# ─── بانر الهيدر ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-hero">  
    <div class="app-hero-icon">🐑</div>  
    <div>  
        <p class="app-hero-title">Sheep Manager Pro</p>  
        <p class="app-hero-subtitle">إدارة القطيع، التطعيمات، والسجل الطبي في مكان واحد</p>  
    </div>  
</div>  
""", unsafe_allow_html=True)

# عرض رسائل النجاح الثابتة في حال وجودها بعد التحديث
if st.session_state.success_msg:
    st.success(st.session_state.success_msg)
    st.session_state.success_msg = None

# ─── إدارة البيانات ────────────────────────────────────────────────────────
DATA_FILE = "herd_data.json"
HISTORY_FILE = "medical_history.json"
REQUIRED_COLS = ["ID", "القلادة", "الجنس", "العمر", "وحدة", "عدد الولادات", "صورة", "اللقاحات", "الجرعات", "آخر تغطيس", "الأم", "الأبناء"]
HISTORY_COLS = ["ID", "التاريخ", "الإجراء", "العلاج", "الأغنام", "صورة"]

def save_image(uploaded_file):
    if uploaded_file is not None:
        file_path = f"images/{uuid.uuid4()}.jpg"
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return file_path
    return ""

def safe_delete_image(path):
    if path and isinstance(path, str) and os.path.exists(path):
        try: os.remove(path)
        except OSError: pass

def safe_literal_eval(value, default=None):
    if default is None: default = []
    try:
        result = ast.literal_eval(value)
        return result if isinstance(result, list) else default
    except (ValueError, SyntaxError, TypeError):
        return default

def load_data(file, columns):
    if not os.path.exists(file): return pd.DataFrame(columns=columns)
    try:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            df = pd.DataFrame(data)
            for col in columns:
                if col not in df.columns:
                    if col in ["الأبناء", "اللقاحات", "الجرعات"]: df[col] = "[]"
                    elif col == "وحدة": df[col] = "شهر"
                    else: df[col] = ""
            return df
    except Exception:
        return pd.DataFrame(columns=columns)

def save_data(df, file):
    df.to_json(file, orient="records", force_ascii=False, indent=4)

if "herd" not in st.session_state:
    st.session_state.herd = load_data(DATA_FILE, REQUIRED_COLS)
if "history" not in st.session_state:
    st.session_state.history = load_data(HISTORY_FILE, HISTORY_COLS)

def get_collar_by_id(sheep_id):
    if not sheep_id: return ""
    row = st.session_state.herd[st.session_state.herd["ID"] == sheep_id]
    return row.iloc[0]["القلادة"] if not row.empty else "(محذوف)"

def format_sheep_label(sheep_id):
    row = st.session_state.herd[st.session_state.herd["ID"] == sheep_id]
    if row.empty: return sheep_id
    row = row.iloc[0]
    return f"{row['القلادة']} ({row['الجنس']})"

# ─── واجهة التطبيق ─────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["🏠 القطيع", "💉 إجراء طبي", "📋 السجل", "➕ إدارة النظام"])

# ─── 1. القطيع ───
with tab1:
    st.subheader("📊 إحصائيات القطيع")
    df = st.session_state.herd
    if not df.empty:  
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🐑 العدد الكلي", len(df))
        col2.metric("♂️ ذكور", len(df[df["الجنس"].isin(["ذكر", "ذكر صغير"])]))
        col3.metric("♀️ إناث", len(df[df["الجنس"].isin(["أنثى", "أنثى صغيرة"])]))
        col4.metric("👶 صغار", len(df[df["الجنس"].str.contains("صغير", na=False)]))
        st.divider()  
        
        for idx, row in df.iterrows():  
            kids_ids = safe_literal_eval(row.get('الأبناء', '[]'))  
            with st.expander(f"🏷️ القلادة: {row['القلادة']} | {row['الجنس']}"):  
                col_img, col_info = st.columns([1, 3])  
                with col_img:  
                    if row.get('صورة') and os.path.exists(row['صورة']):  
                        st.image(row['صورة'], use_container_width=True)  
                with col_info:  
                    st.markdown(f"""  
                    <span class="ear-tag">{'♀️' if 'أنثى' in row['الجنس'] else '♂️'} {row['الجنس']}</span>  
                    <span class="info-chip">🗓️ {row['العمر']} {row.get('وحدة', 'شهر')}</span>  
                    <span class="info-chip">🐑 {row.get('عدد الولادات', 0)} ولادات</span>  
                    """, unsafe_allow_html=True)  
                    if row.get('الأم'): st.markdown(f"👩 **الأم:** {get_collar_by_id(row['الأم'])}")
                    if kids_ids:
                        k_names = [get_collar_by_id(k) for k in kids_ids]
                        st.markdown(f"👶 **الأبناء:** {', '.join(k_names)}")
    else:  
        st.info("القطيع فارغ. اذهب إلى تبويب (إدارة النظام) لإضافة أغنام.")

# ─── 2. إجراء طبي ───
with tab2:
    st.subheader("💉 تسجيل إجراء طبي جديد")
    if not st.session_state.herd.empty:
        herd_ids = st.session_state.herd["ID"].tolist()
        selected_ids = st.multiselect("اختر الأغنام المستهدفة:", herd_ids, format_func=format_sheep_label)
        action_type = st.radio("نوع الإجراء:", ["تطعيم", "جرعة طفيلية", "تغطيس"], horizontal=True)
        
        opts = ['إيفومك', 'معوي/دموي', 'طاعون', 'جدري'] if action_type == "تطعيم" else (['جرعة كبدية', 'جرعة معوية'] if action_type == "جرعة طفيلية" else ['تغطيس شامل'])
        treatment = st.selectbox("العلاج:", opts)
        date = str(st.date_input("التاريخ:"))
        img_file = st.file_uploader("صورة التوثيق (اختياري)", type=['jpg', 'png'])
        
        if st.button("💾 حفظ الإجراء"):
            if selected_ids:
                new_hist = pd.DataFrame([{
                    "ID": str(uuid.uuid4()), "التاريخ": date, "الإجراء": action_type,
                    "العلاج": treatment, "الأغنام": ", ".join([get_collar_by_id(sid) for sid in selected_ids]),
                    "صورة": save_image(img_file)
                }])
                st.session_state.history = pd.concat([st.session_state.history, new_hist], ignore_index=True)
                save_data(st.session_state.history, HISTORY_FILE)
                st.session_state.success_msg = "💉 تم تسجيل الإجراء الطبي بنجاح!"
                st.rerun()
            else:
                st.warning("الرجاء اختيار رأس واحد على الأقل.")
    else:
        st.warning("يجب إضافة أغنام أولاً.")

# ─── 3. السجل الطبي ───
with tab3:
    st.subheader("📋 السجل الطبي")
    
    # تقسيم السجل الطبي لتبويبين: عرض وتعديل
    hist_tab1, hist_tab2 = st.tabs(["🔍 عرض السجلات", "✏️ تعديل سجل"])
    
    with hist_tab1:
        if not st.session_state.history.empty:
            for idx, row in st.session_state.history.iterrows():
                with st.expander(f"🗓️ {row['التاريخ']} | {row['الإجراء']} ({row['العلاج']})"):
                    st.write(f"**الأغنام المعالجة:** {row['الأغنام']}")
                    if row.get('صورة') and os.path.exists(row['صورة']):
                        st.image(row['صورة'], width=200)
                    
                    if st.button(f"🗑️ حذف السجل", key=f"del_hist_{idx}", type="primary"):
                        safe_delete_image(row.get('صورة'))
                        st.session_state.history = st.session_state.history.drop(idx).reset_index(drop=True)
                        save_data(st.session_state.history, HISTORY_FILE)
                        st.session_state.success_msg = "🗑️ تم حذف السجل الطبي بنجاح!"
                        st.rerun()
        else:
            st.info("لا توجد سجلات طبية حتى الآن.")
            
    with hist_tab2:
        if not st.session_state.history.empty:
            def format_hist_label(hist_idx):
                h_row = st.session_state.history.iloc[hist_idx]
                h_sheep = str(h_row.get('الأغنام', ''))
                return f"🗓️ {h_row['التاريخ']} - {h_row['الإجراء']} ({h_row['العلاج']}) - الأغنام: {h_sheep[:30]}..."
                
            hist_indices = list(range(len(st.session_state.history)))
            selected_hist_idx = st.selectbox("اختر السجل الطبي المراد تعديله:", hist_indices, format_func=format_hist_label)
            
            if selected_hist_idx is not None:
                hist_row = st.session_state.history.iloc[selected_hist_idx]
                
                with st.form("edit_history_form"):
                    st.markdown("### ✏️ تعديل بيانات السجل الطبي")
                    
                    try:
                        curr_date = datetime.strptime(str(hist_row["التاريخ"]), "%Y-%m-%d").date()
                    except ValueError:
                        curr_date = datetime.today().date()
                    new_date = st.date_input("التاريخ:", value=curr_date)
                    
                    action_opts = ["تطعيم", "جرعة طفيلية", "تغطيس"]
                    curr_action = hist_row.get("الإجراء", "تطعيم")
                    a_idx = action_opts.index(curr_action) if curr_action in action_opts else 0
                    new_action_type = st.radio("نوع الإجراء:", action_opts, index=a_idx, horizontal=True)
                    
                    all_opts = ['إيفومك', 'معوي/دموي', 'طاعون', 'جدري', 'جرعة كبدية', 'جرعة معوية', 'تغطيس شامل']
                    curr_treatment = hist_row.get("العلاج", "")
                    t_idx = all_opts.index(curr_treatment) if curr_treatment in all_opts else 0
                    new_treatment = st.selectbox("العلاج:", all_opts, index=t_idx)
                    
                    herd_ids = st.session_state.herd["ID"].tolist()
                    saved_collars = [c.strip() for c in str(hist_row['الأغنام']).split(",")]
                    default_ids = []
                    for sid in herd_ids:
                        if get_collar_by_id(sid) in saved_collars:
                            default_ids.append(sid)
                            
                    new_selected_ids = st.multiselect(
                        "اختر الأغنام المستهدفة:", 
                        herd_ids, 
                        default=default_ids, 
                        format_func=format_sheep_label
                    )
                    
                    new_hist_img = st.file_uploader("تحديث صورة التوثيق (اتركه فارغاً للاحتفاظ بالصورة الحالية)", type=['jpg', 'png'])
                    
                    if st.form_submit_button("💾 حفظ التعديلات على السجل"):
                        if new_selected_ids:
                            st.session_state.history.at[selected_hist_idx, "التاريخ"] = str(new_date)
                            st.session_state.history.at[selected_hist_idx, "الإجراء"] = new_action_type
                            st.session_state.history.at[selected_hist_idx, "العلاج"] = new_treatment
                            st.session_state.history.at[selected_hist_idx, "الأغنام"] = ", ".join([get_collar_by_id(sid) for sid in new_selected_ids])
                            
                            if new_hist_img:
                                safe_delete_image(hist_row.get("صورة"))
                                st.session_state.history.at[selected_hist_idx, "صورة"] = save_image(new_hist_img)
                                
                            save_data(st.session_state.history, HISTORY_FILE)
                            st.session_state.success_msg = "✏️ تم تعديل السجل الطبي بنجاح! ✅"
                            st.rerun()
                        else:
                            st.error("الرجاء اختيار رأس واحد على الأقل.")
        else:
            st.info("لا توجد سجلات طبية لتعديلها.")

# ─── 4. إدارة النظام ───
with tab4:
    mng_tab1, mng_tab2, mng_tab3 = st.tabs(["➕ إضافة رأس جديد", "✏️ تعديل / حذف", "💾 النسخ الاحتياطي"])
    
    with mng_tab1:
        with st.form("add_sheep_form"):
            col1, col2 = st.columns(2)
            collar = col1.text_input("القلادة (الرقم أو الاسم)*")
            gender = col2.selectbox("الجنس*", ["أنثى", "أنثى صغيرة", "ذكر", "ذكر صغير"])
            
            col3, col4, col5 = st.columns(3)
            age = col3.number_input("العمر", min_value=0)
            unit = col4.selectbox("الوحدة", ["شهر", "سنة"])
            births = col5.number_input("عدد الولادات", min_value=0)
            
            mother = st.selectbox("الأم (اختياري)", [None] + st.session_state.herd["ID"].tolist(), format_func=lambda x: "بدون أم مسجلة" if x is None else format_sheep_label(x))
            img = st.file_uploader("صورة (اختياري)", type=['jpg', 'png'], key="new_img")
            
            if st.form_submit_button("➕ حفظ وإضافة للقطيع"):
                if collar:
                    new_id = str(uuid.uuid4())
                    new_sheep = pd.DataFrame([{
                        "ID": new_id, "القلادة": collar, "الجنس": gender, "العمر": age,
                        "وحدة": unit, "عدد الولادات": births, "الأم": mother or "",
                        "الأبناء": "[]", "صورة": save_image(img),
                        "اللقاحات": "[]", "الجرعات": "[]", "آخر تغطيس": ""
                    }])
                    st.session_state.herd = pd.concat([st.session_state.herd, new_sheep], ignore_index=True)
                    
                    if mother:
                        m_idx = st.session_state.herd[st.session_state.herd["ID"] == mother].index[0]
                        kids = safe_literal_eval(st.session_state.herd.at[m_idx, "الأبناء"])
                        kids.append(new_id)
                        st.session_state.herd.at[m_idx, "الأبناء"] = str(kids)
                        
                    save_data(st.session_state.herd, DATA_FILE)
                    st.session_state.success_msg = "🐑 تمت إضافة رأس جديد للقطيع بنجاح! ✅"
                    st.rerun()
                else:
                    st.error("الرجاء إدخال رقم/اسم القلادة.")

    with mng_tab2:
        if not st.session_state.herd.empty:
            edit_target = st.selectbox("اختر الرأس للتعديل أو الحذف:", st.session_state.herd["ID"].tolist(), format_func=format_sheep_label)
            
            if edit_target:
                target_idx = st.session_state.herd[st.session_state.herd["ID"] == edit_target].index[0]
                target_data = st.session_state.herd.iloc[target_idx]
                
                with st.form("edit_sheep_form"):
                    st.markdown("### ✏️ تعديل بيانات الرأس")
                    c1, c2 = st.columns(2)
                    new_collar = c1.text_input("القلادة (الرقم أو الاسم)*", value=target_data.get("القلادة", ""))
                    
                    gender_opts = ["أنثى", "أنثى صغيرة", "ذكر", "ذكر صغير"]
                    curr_gender = target_data.get("الجنس", "أنثى")
                    g_idx = gender_opts.index(curr_gender) if curr_gender in gender_opts else 0
                    new_gender = c2.selectbox("الجنس*", gender_opts, index=g_idx)
                    
                    c3, c4, c5 = st.columns(3)
                   
