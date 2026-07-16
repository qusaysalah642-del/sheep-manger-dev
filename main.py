# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import json
import os
import uuid
import ast
import time
import logging
from datetime import datetime, date
from PIL import Image

# ─── إعداد التسجيل ──────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# ─── إعداد الصفحة ──────────────────────────────────────────────────────
st.set_page_config(page_title="Sheep Manager Pro", page_icon="🐑", layout="wide")

# ─── تهيئة Session State ──────────────────────────────────────────────
for key in ["success_msg", "toast", "editing_hist_id", "splash_shown"]:
    if key not in st.session_state:
        st.session_state[key] = None

# ─── شاشة ترحيب ──────────────────────────────────────────────────────
if not st.session_state.splash_shown:
    st.markdown("""
    <div id="splash" style="position:fixed; top:0; left:0; width:100%; height:100%; background:#0b1f16; display:flex; flex-direction:column; align-items:center; justify-content:center; z-index:9999; animation: fadeOut 2s ease-in forwards; animation-delay:1.5s;">
        <div style="font-size:80px; background:#d3a15c; width:120px; height:120px; border-radius:30px; display:flex; align-items:center; justify-content:center; box-shadow:0 0 40px rgba(211,161,92,0.3);">🐑</div>
        <h1 style="color:white; font-size:32px; margin-top:20px;">Sheep Manager Pro</h1>
        <p style="color:#93b3a1; font-size:16px;">إدارة القطيع، التطعيمات، والسجل الطبي</p>
    </div>
    <style>
        @keyframes fadeOut {
            0% { opacity: 1; }
            100% { opacity: 0; pointer-events: none; }
        }
    </style>
    <script>
        setTimeout(() => {
            document.getElementById('splash').style.display = 'none';
        }, 3000);
    </script>
    """, unsafe_allow_html=True)
    st.session_state.splash_shown = True

if st.session_state.toast:
    st.toast(st.session_state.toast)
    st.session_state.toast = None

# ─── إنشاء المجلدات ──────────────────────────────────────────────────
for folder in ["images", "backups", "data"]:
    os.makedirs(folder, exist_ok=True)

# ─── دوال مساعدة ──────────────────────────────────────────────────────

def safe_literal_eval(value, default=None):
    if default is None:
        default = []
    if value is None or value == "":
        return default
    try:
        if isinstance(value, list):
            return value
        result = ast.literal_eval(value)
        return result if isinstance(result, list) else default
    except (ValueError, SyntaxError, TypeError):
        return default

def calculate_age(birth_date_str):
    if not birth_date_str:
        return "غير محدد", 0
    try:
        birth = datetime.strptime(birth_date_str, "%Y-%m-%d").date()
        today = date.today()
        delta = today - birth
        total_months = delta.days // 30
        years = total_months // 12
        months = total_months % 12
        if years > 0:
            return f"{years} سنة و {months} شهر", years + (months/12)
        else:
            return f"{months} شهر", months/12 if months else 0.1
    except Exception:
        return "غير محدد", 0

def save_image_compressed(uploaded_file, max_size=(800, 800)):
    if uploaded_file is not None:
        try:
            img = Image.open(uploaded_file)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            path = f"images/{uuid.uuid4()}.jpg"
            img.save(path, "JPEG", quality=85, optimize=True)
            return path
        except Exception:
            return ""
    return ""

def safe_delete_image(path):
    if path and os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass

def load_data(file, columns):
    if not os.path.exists(file):
        return pd.DataFrame(columns=columns)
    try:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            df = pd.DataFrame(data)
            for col in columns:
                if col not in df.columns:
                    if col in ["الأبناء", "اللقاحات", "الجرعات"]:
                        df[col] = "[]"
                    elif col == "تاريخ الميلاد":
                        df[col] = ""
                    elif col == "ملاحظات":
                        df[col] = ""
                    else:
                        df[col] = ""
            return df
    except Exception:
        return pd.DataFrame(columns=columns)

def save_data(df, file):
    df.to_json(file, orient="records", force_ascii=False, indent=4)

def auto_backup():
    date_str = datetime.now().strftime("%Y-%m-%d")
    backup_file = f"backups/auto_backup_{date_str}.json"
    if not os.path.exists(backup_file):
        try:
            backup_dict = {
                "herd": st.session_state.herd.to_dict(orient="records"),
                "history": st.session_state.history.to_dict(orient="records"),
                "timestamp": datetime.now().isoformat()
            }
            with open(backup_file, "w", encoding="utf-8") as f:
                json.dump(backup_dict, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

def validate_sheep_data(data):
    errors = []
    if not data.get("القلادة"):
        errors.append("القلادة مطلوبة")
    if data.get("الجنس") not in ["أنثى", "أنثى صغيرة", "ذكر", "ذكر صغير"]:
        errors.append("الجنس غير صحيح")
    if data.get("عدد الولادات", 0) < 0:
        errors.append("عدد الولادات لا يمكن أن يكون سالباً")
    birth = data.get("تاريخ الميلاد")
    if birth:
        try:
            datetime.strptime(birth, "%Y-%m-%d")
        except ValueError:
            errors.append("صيغة تاريخ الميلاد غير صحيحة")
    return errors

def get_collar_by_id(sheep_id):
    if not sheep_id:
        return ""
    row = st.session_state.herd[st.session_state.herd["ID"] == sheep_id]
    return row.iloc[0]["القلادة"] if not row.empty else "(محذوف)"

def format_sheep_label(sheep_id):
    row = st.session_state.herd[st.session_state.herd["ID"] == sheep_id]
    if row.empty:
        return sheep_id
    row = row.iloc[0]
    return f"{row['القلادة']} ({row['الجنس']})"

def show_notification(message, type="info"):
    icons = {"success": "✅", "error": "❌", "warning": "⚠️", "info": "ℹ️"}
    st.session_state.toast = f"{icons.get(type, '')} {message}"

# ─── تحميل البيانات ──────────────────────────────────────────────────
DATA_FILE = "data/herd_data.json"
HISTORY_FILE = "data/medical_history.json"
REQUIRED_COLS = ["ID", "القلادة", "الجنس", "تاريخ الميلاد", "عدد الولادات", "صورة", "اللقاحات", "الجرعات", "آخر تغطيس", "الأم", "الأبناء", "ملاحظات"]
HISTORY_COLS = ["ID", "التاريخ", "الإجراء", "العلاج", "الأغنام", "صورة"]

if "herd" not in st.session_state:
    st.session_state.herd = load_data(DATA_FILE, REQUIRED_COLS)
if "history" not in st.session_state:
    st.session_state.history = load_data(HISTORY_FILE, HISTORY_COLS)

auto_backup()
# ─── CSS مع أنيميشن وتحسين البطاقات ─────────────────────────────────
st.markdown("""
<style>
    body { direction: rtl; }
    .stApp { background: #0b1f16; color: #eef6f0; }
    
    /* أنيميشن للحقول */
    .stTextInput input, .stNumberInput input, .stDateInput input, .stSelectbox div[data-baseweb="select"] > div {
        transition: all 0.3s ease;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 10px !important;
        background: #0b1f16 !important;
        color: #eef6f0 !important;
    }
    .stTextInput input:focus, .stNumberInput input:focus, .stDateInput input:focus {
        border-color: #4c9a6a !important;
        box-shadow: 0 0 15px rgba(76,154,106,0.2) !important;
        transform: scale(1.02);
    }
    
    /* أنيميشن للأزرار */
    .stButton > button {
        background: linear-gradient(135deg, #4c9a6a 0%, #2f6b48 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 10px 0;
        width: 100%;
        transition: all 0.3s ease;
        font-weight: 700;
    }
    .stButton > button:hover {
        transform: scale(1.05) translateY(-2px);
        box-shadow: 0 8px 25px rgba(76,154,106,0.3);
    }
    .stButton > button:active {
        transform: scale(0.95);
    }
    
    /* أنيميشن للبطاقات */
    [data-testid="stExpander"] {
        background: #123326;
        border-radius: 14px;
        border: 1px solid rgba(255,255,255,0.08);
        transition: all 0.3s ease;
    }
    [data-testid="stExpander"]:hover {
        border-color: #4c9a6a;
        transform: translateX(-3px);
        box-shadow: 0 4px 20px rgba(76,154,106,0.1);
    }
    
    /* أنيميشن للتبويبات */
    .stTabs [data-baseweb="tab"] {
        background: #123326;
        color: #93b3a1;
        border-radius: 20px;
        padding: 8px 16px;
        transition: all 0.3s ease;
        border: 1px solid transparent;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background: #1a4a3a;
        transform: translateY(-2px);
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #4c9a6a 0%, #2f6b48 100%) !important;
        color: white !important;
        border-color: #4c9a6a !important;
        box-shadow: 0 4px 15px rgba(76,154,106,0.3);
    }
    
    /* أنيميشن للصورة */
    .stImage img {
        transition: all 0.5s ease;
        border-radius: 10px;
    }
    .stImage img:hover {
        transform: scale(1.05);
        box-shadow: 0 8px 30px rgba(0,0,0,0.5);
    }
    
    .edit-mode {
        background: #1a3a2a;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #4c9a6a;
        animation: slideIn 0.5s ease;
    }
    @keyframes slideIn {
        0% { opacity: 0; transform: translateX(-20px); }
        100% { opacity: 1; transform: translateX(0); }
    }
    
    /* ─── بطاقات الإحصائيات الأفقية ─── */
    .stats-container {
        display: flex;
        gap: 15px;
        flex-wrap: wrap;
        justify-content: space-around;
        margin-bottom: 20px;
    }
    .stat-card {
        background: #123326;
        border-radius: 16px;
        padding: 18px 25px;
        flex: 1;
        min-width: 150px;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.06);
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    .stat-card:hover {
        transform: translateY(-5px);
        border-color: #4c9a6a;
        box-shadow: 0 8px 30px rgba(76,154,106,0.15);
    }
    .stat-icon {
        font-size: 28px;
        display: block;
        margin-bottom: 5px;
    }
    .stat-number {
        font-size: 32px;
        font-weight: 800;
        color: white;
        line-height: 1.2;
    }
    .stat-label {
        font-size: 14px;
        color: #93b3a1;
        margin-top: 4px;
    }
    .stat-card.green .stat-number { color: #4c9a6a; }
    .stat-card.blue .stat-number { color: #4a90d9; }
    .stat-card.pink .stat-number { color: #e87a7a; }
    .stat-card.gold .stat-number { color: #d3a15c; }
</style>
""", unsafe_allow_html=True)

# ─── الهيدر ──────────────────────────────────────────────────────────
st.markdown("""
<div style="display:flex; align-items:center; gap:15px; background:#123326; padding:20px; border-radius:18px; margin-bottom:20px; animation: fadeIn 0.8s ease;">
    <div style="font-size:40px; background:#d3a15c; width:60px; height:60px; border-radius:15px; display:flex; align-items:center; justify-content:center; box-shadow:0 4px 20px rgba(211,161,92,0.2);">🐑</div>
    <div>
        <h1 style="margin:0; color:white;">Sheep Manager Pro</h1>
        <p style="margin:0; color:#93b3a1;">إدارة القطيع، التطعيمات، والسجل الطبي</p>
    </div>
</div>
<style>
    @keyframes fadeIn {
        0% { opacity: 0; transform: translateY(-20px); }
        100% { opacity: 1; transform: translateY(0); }
    }
</style>
""", unsafe_allow_html=True)

if st.session_state.success_msg:
    st.success(st.session_state.success_msg)
    st.session_state.success_msg = None

# ─── تعريف خيارات العلاج ────────────────────────────────────────────
TREATMENT_OPTS = {
    'تطعيم': ['إيفومك', 'معوي/دموي', 'طاعون', 'جدري'],
    'جرعة طفيلية': ['جرعة كبدية', 'جرعة معوية'],
    'تغطيس': ['تغطيس شامل']
}

# ─── الأقسام الرئيسية ──────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["🏠 القطيع", "💉 إجراء طبي", "📋 السجل", "➕ إدارة النظام"])

# ─── 1. القطيع (مع بطاقات إحصائيات أفقية وترقيم الأبناء) ───
with tab1:
    st.subheader("📊 إحصائيات القطيع")
    df = st.session_state.herd
    if not df.empty:
        total = len(df)
        males = len(df[df["الجنس"].isin(["ذكر", "ذكر صغير"])])
        females = len(df[df["الجنس"].isin(["أنثى", "أنثى صغيرة"])])
        young = len(df[df["الجنس"].str.contains("صغير", na=False)])

        # عرض البطاقات الأفقية
        st.markdown(f"""
        <div class="stats-container">
            <div class="stat-card green">
                <span class="stat-icon">🐑</span>
                <div class="stat-number">{total}</div>
                <div class="stat-label">العدد الكلي</div>
            </div>
            <div class="stat-card blue">
                <span class="stat-icon">♂️</span>
                <div class="stat-number">{males}</div>
                <div class="stat-label">ذكور</div>
            </div>
            <div class="stat-card pink">
                <span class="stat-icon">♀️</span>
                <div class="stat-number">{females}</div>
                <div class="stat-label">إناث</div>
            </div>
            <div class="stat-card gold">
                <span class="stat-icon">👶</span>
                <div class="stat-number">{young}</div>
                <div class="stat-label">صغار</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        search_term = st.text_input("🔍 بحث بالقلادة", placeholder="اكتب للبحث...")
        filtered_df = df.copy()
        if search_term:
            filtered_df = filtered_df[filtered_df["القلادة"].str.contains(search_term, case=False, na=False)]

        if filtered_df.empty:
            st.info("لا توجد نتائج")
        else:
            for _, row in filtered_df.iterrows():
                birth = row.get("تاريخ الميلاد", "")
                age_str, _ = calculate_age(birth)

                with st.expander(f"🏷️ {row['القلادة']} - {row['الجنس']}"):
                    col_img, col_info = st.columns([1, 2])
                    with col_img:
                        if row.get('صورة') and os.path.exists(row['صورة']):
                            st.image(row['صورة'], width=150)
                    with col_info:
                        st.write(f"**العمر:** {age_str}")
                        st.write(f"**عدد الولادات:** {row.get('عدد الولادات', 0)}")
                        if row.get('الأم'):
                            st.write(f"**الأم:** {get_collar_by_id(row['الأم'])}")
                        if row.get('ملاحظات'):
                            st.write(f"**📝 ملاحظات:** {row['ملاحظات']}")
                        
                        # ─── عرض الأبناء مع ترقيم ───
                        if row.get('الأبناء'):
                            kids = safe_literal_eval(row['الأبناء'])
                            if kids:
                                kids_names = []
                                for i, kid_id in enumerate(kids, 1):
                                    name = get_collar_by_id(kid_id)
                                    if name and name != "(محذوف)":
                                        kids_names.append(f"{i}. {name}")
                                if kids_names:
                                    st.write(f"**الأبناء:** {', '.join(kids_names)}")
                                else:
                                    st.write("**الأبناء:** لا يوجد")
    else:
        st.info("القطيع فارغ.")
        # ─── 2. إجراء طبي ───
with tab2:
    st.subheader("💉 تسجيل إجراء طبي")
    if not st.session_state.herd.empty:
        herd_ids = st.session_state.herd["ID"].tolist()
        selected = st.multiselect("اختر الأغنام:", herd_ids, format_func=format_sheep_label)
        
        action = st.radio("النوع:", ["تطعيم", "جرعة طفيلية", "تغطيس"], horizontal=True)
        available_treatments = TREATMENT_OPTS.get(action, [])
        treatment = st.selectbox("العلاج:", available_treatments)
        
        date = str(st.date_input("التاريخ:"))
        img = st.file_uploader("صورة (اختياري)", type=['jpg','png'])

        if st.button("💾 حفظ"):
            if selected:
                new = pd.DataFrame([{
                    "ID": str(uuid.uuid4()),
                    "التاريخ": date,
                    "الإجراء": action,
                    "العلاج": treatment,
                    "الأغنام": ", ".join([get_collar_by_id(s) for s in selected]),
                    "صورة": save_image_compressed(img)
                }])
                st.session_state.history = pd.concat([st.session_state.history, new], ignore_index=True)
                save_data(st.session_state.history, HISTORY_FILE)
                show_notification("تم الحفظ!", "success")
                time.sleep(0.5)
                st.rerun()
            else:
                st.warning("اختر رأساً واحداً على الأقل.")
    else:
        st.warning("أضف أغناماً أولاً.")

# ─── 3. السجل الطبي ───
with tab3:
    st.subheader("📋 السجل الطبي")
    if not st.session_state.history.empty:
        editing_id = st.session_state.get("editing_hist_id", None)

        for idx, row in st.session_state.history.iterrows():
            is_editing = (editing_id == row["ID"])

            with st.expander(f"🗓️ {row['التاريخ']} - {row['الإجراء']} ({row['العلاج']})", expanded=is_editing):
                if is_editing:
                    st.markdown('<div class="edit-mode">', unsafe_allow_html=True)
                    st.markdown("#### ✏️ تعديل السجل")
                    
                    try:
                        curr_date = datetime.strptime(str(row["التاريخ"]), "%Y-%m-%d").date()
                    except:
                        curr_date = date.today()
                    
                    curr_action = row.get("الإجراء", "تطعيم")
                    curr_treatment = row.get("العلاج", "")
                    
                    radio_key = f"action_radio_{row['ID']}"
                    new_action = st.radio(
                        "نوع الإجراء:",
                        ["تطعيم", "جرعة طفيلية", "تغطيس"],
                        index=["تطعيم", "جرعة طفيلية", "تغطيس"].index(curr_action),
                        horizontal=True,
                        key=radio_key
                    )
                    
                    available_treatments = TREATMENT_OPTS.get(new_action, [])
                    if curr_treatment in available_treatments:
                        t_idx = available_treatments.index(curr_treatment)
                    else:
                        t_idx = 0
                    
                    with st.form(key=f"edit_form_{row['ID']}"):
                        new_date = st.date_input("التاريخ:", value=curr_date)
                        new_treatment = st.selectbox("العلاج:", available_treatments, index=t_idx)

                        herd_ids = st.session_state.herd["ID"].tolist()
                        saved_collars = [c.strip() for c in str(row['الأغنام']).split(",")]
                        default_ids = []
                        for sid in herd_ids:
                            if get_collar_by_id(sid) in saved_collars:
                                default_ids.append(sid)

                        new_selected = st.multiselect(
                            "اختر الأغنام المستهدفة:",
                            herd_ids,
                            default=default_ids,
                            format_func=format_sheep_label
                        )

                        new_img = st.file_uploader("تحديث الصورة (اتركه فارغاً للاحتفاظ بالصورة الحالية)", type=['jpg','png'])

                        col_btn1, col_btn2 = st.columns(2)
                        with col_btn1:
                            if st.form_submit_button("💾 حفظ التعديلات"):
                                if new_selected:
                                    st.session_state.history.at[idx, "التاريخ"] = str(new_date)
                                    st.session_state.history.at[idx, "الإجراء"] = new_action
                                    st.session_state.history.at[idx, "العلاج"] = new_treatment
                                    st.session_state.history.at[idx, "الأغنام"] = ", ".join([get_collar_by_id(s) for s in new_selected])
                                    if new_img:
                                        safe_delete_image(row.get("صورة"))
                                        st.session_state.history.at[idx, "صورة"] = save_image_compressed(new_img)
                                    save_data(st.session_state.history, HISTORY_FILE)
                                    st.session_state.editing_hist_id = None
                                    show_notification("تم تحديث السجل!", "success")
                                    time.sleep(0.5)
                                    st.rerun()
                                else:
                                    st.error("الرجاء اختيار رأس واحد على الأقل.")
                        with col_btn2:
                            if st.form_submit_button("❌ إلغاء"):
                                st.session_state.editing_hist_id = None
                                st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.write(f"**الأغنام:** {row['الأغنام']}")
                    if row.get('صورة') and os.path.exists(row['صورة']):
                        st.image(row['صورة'], width=150)

                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.button(f"✏️ تعديل", key=f"edit_btn_{row['ID']}"):
                            st.session_state.editing_hist_id = row["ID"]
                            st.rerun()
                    with col_btn2:
                        if st.button(f"🗑️ حذف", key=f"del_btn_{row['ID']}", type="primary"):
                            safe_delete_image(row.get('صورة'))
                            st.session_state.history = st.session_state.history.drop(idx).reset_index(drop=True)
                            save_data(st.session_state.history, HISTORY_FILE)
                            show_notification("تم الحذف!", "success")
                            st.rerun()
    else:
        st.info("لا توجد سجلات.")
        # ─── 4. إدارة النظام ───
with tab4:
    m1, m2, m3 = st.tabs(["➕ إضافة", "✏️ تعديل", "💾 نسخ احتياطي"])
    with m1:
        with st.form("add"):
            c1, c2 = st.columns(2)
            collar = c1.text_input("القلادة*")
            gender = c2.selectbox("الجنس*", ["أنثى", "أنثى صغيرة", "ذكر", "ذكر صغير"])
            birth_date = st.date_input("تاريخ الميلاد", value=None)
            births = st.number_input("عدد الولادات", min_value=0)
            mother = st.selectbox("الأم", [None] + st.session_state.herd["ID"].tolist(),
                                  format_func=lambda x: "بدون" if x is None else format_sheep_label(x))
            notes = st.text_area("ملاحظات", placeholder="أي ملاحظات إضافية...")
            img = st.file_uploader("صورة", type=['jpg','png'])
            if st.form_submit_button("➕ إضافة"):
                if collar:
                    birth_str = birth_date.strftime("%Y-%m-%d") if birth_date else ""
                    data = {"القلادة": collar, "الجنس": gender, "تاريخ الميلاد": birth_str, "عدد الولادات": births}
                    errors = validate_sheep_data(data)
                    if errors:
                        for e in errors:
                            st.error(f"❌ {e}")
                    else:
                        new_id = str(uuid.uuid4())
                        new_row = pd.DataFrame([{
                            "ID": new_id,
                            "القلادة": collar,
                            "الجنس": gender,
                            "تاريخ الميلاد": birth_str,
                            "عدد الولادات": births,
                            "الأم": mother or "",
                            "الأبناء": "[]",
                            "ملاحظات": notes,
                            "صورة": save_image_compressed(img),
                            "اللقاحات": "[]",
                            "الجرعات": "[]",
                            "آخر تغطيس": ""
                        }])
                        st.session_state.herd = pd.concat([st.session_state.herd, new_row], ignore_index=True)
                        if mother:
                            m_idx = st.session_state.herd[st.session_state.herd["ID"] == mother].index[0]
                            kids = safe_literal_eval(st.session_state.herd.at[m_idx, "الأبناء"])
                            kids.append(new_id)
                            st.session_state.herd.at[m_idx, "الأبناء"] = str(kids)
                        save_data(st.session_state.herd, DATA_FILE)
                        show_notification("تمت الإضافة!", "success")
                        st.rerun()
                else:
                    st.error("القلادة مطلوبة")

    with m2:
        if not st.session_state.herd.empty:
            target = st.selectbox("اختر رأساً:", st.session_state.herd["ID"].tolist(), format_func=format_sheep_label)
            if target:
                idx = st.session_state.herd[st.session_state.herd["ID"] == target].index[0]
                row = st.session_state.herd.iloc[idx]
                with st.form("edit"):
                    new_collar = st.text_input("القلادة*", value=row["القلادة"])
                    new_gender = st.selectbox("الجنس*", ["أنثى","أنثى صغيرة","ذكر","ذكر صغير"],
                                              index=["أنثى","أنثى صغيرة","ذكر","ذكر صغير"].index(row["الجنس"]))
                    current_birth = row.get("تاريخ الميلاد", "")
                    if current_birth:
                        try:
                            default_date = datetime.strptime(current_birth, "%Y-%m-%d").date()
                        except:
                            default_date = None
                    else:
                        default_date = None
                    new_birth = st.date_input("تاريخ الميلاد", value=default_date)
                    new_births = st.number_input("عدد الولادات", min_value=0, value=int(row["عدد الولادات"]))
                    new_mother = st.selectbox("الأم", [None] + st.session_state.herd["ID"].tolist(),
                                              index=([None] + st.session_state.herd["ID"].tolist()).index(row.get("الأم")) if row.get("الأم") in [None] + st.session_state.herd["ID"].tolist() else 0,
                                              format_func=lambda x: "بدون" if x is None else format_sheep_label(x))
                    new_notes = st.text_area("ملاحظات", value=row.get("ملاحظات", ""))
                    new_img = st.file_uploader("تحديث الصورة", type=['jpg','png'])
                    if st.form_submit_button("💾 حفظ"):
                        st.session_state.herd.at[idx, "القلادة"] = new_collar
                        st.session_state.herd.at[idx, "الجنس"] = new_gender
                        st.session_state.herd.at[idx, "تاريخ الميلاد"] = new_birth.strftime("%Y-%m-%d") if new_birth else ""
                        st.session_state.herd.at[idx, "عدد الولادات"] = new_births
                        st.session_state.herd.at[idx, "الأم"] = new_mother or ""
                        st.session_state.herd.at[idx, "ملاحظات"] = new_notes
                        if new_img:
                            safe_delete_image(row.get("صورة"))
                            st.session_state.herd.at[idx, "صورة"] = save_image_compressed(new_img)
                        save_data(st.session_state.herd, DATA_FILE)
                        show_notification("تم التحديث!", "success")
                        st.rerun()
                if st.button("🗑️ حذف نهائي", type="primary"):
                    safe_delete_image(row.get("صورة"))
                    st.session_state.herd = st.session_state.herd.drop(idx).reset_index(drop=True)
                    save_data(st.session_state.herd, DATA_FILE)
                    show_notification("تم الحذف!", "success")
                    st.rerun()
        else:
            st.info("القطيع فارغ")

    with m3:
        st.download_button("📥 تحميل نسخة احتياطية",
                           data=json.dumps({"herd": st.session_state.herd.to_dict(orient="records"),
                                            "history": st.session_state.history.to_dict(orient="records")},
                                            ensure_ascii=False, indent=2),
                           file_name=f"backup_{datetime.now().strftime('%Y-%m-%d')}.json",
                           mime="application/json")
        uploaded = st.file_uploader("استعادة", type=['json'])
        if uploaded and st.button("🔄 تأكيد الاستعادة", type="primary"):
            try:
                data = json.load(uploaded)
                st.session_state.herd = pd.DataFrame(data.get("herd", []))
                st.session_state.history = pd.DataFrame(data.get("history", []))
                save_data(st.session_state.herd, DATA_FILE)
                save_data(st.session_state.history, HISTORY_FILE)
                show_notification("تمت الاستعادة!", "success")
                st.rerun()
            except Exception as e:
                st.error(f"خطأ: {e}")
