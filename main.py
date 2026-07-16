# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import json
import os
import uuid
import ast
import time
import logging
from datetime import datetime
from PIL import Image

# ─── إعداد التسجيل (Logging) ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

# ─── إعداد الصفحة ────────────────────────────────────────────────────────────
st.set_page_config(page_title="Sheep Manager Pro", page_icon="🐑", layout="wide")

# ─── تهيئة Session State ────────────────────────────────────────────────────
if "success_msg" not in st.session_state:
    st.session_state.success_msg = None
if "toast" not in st.session_state:
    st.session_state.toast = None

# عرض رسائل الإشعار
if st.session_state.toast:
    st.toast(st.session_state.toast)
    st.session_state.toast = None

# ─── نظام الألوان والخطوط ──────────────────────────────────────────────────
C_BG_DEEP = "#0b1f16"
C_BG_PANEL = "#123326"
C_BORDER = "rgba(255,255,255,0.08)"
C_TEXT = "#eef6f0"
C_TEXT_MUTED = "#93b3a1"
C_GREEN = "#4c9a6a"
C_GREEN_DARK = "#2f6b48"
C_AMBER = "#d3a15c"
C_AMBER_DARK = "#a97c3c"
C_DANGER = "#e2665a"
C_BLUE = "#4a90d9"
C_PINK = "#e87a7a"

# ─── إنشاء المجلدات الضرورية ──────────────────────────────────────────────
for folder in ["images", "backups", "data"]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# ─── CSS ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@600;700;800&family=Tajawal:wght@400;500;700&display=swap');

    html, body, [class*="css"] { font-family: 'Tajawal', sans-serif; direction: rtl; text-align: right; }
    h1, h2, h3, .app-hero-title { font-family: 'Cairo', sans-serif; }

    .stApp { background: linear-gradient(180deg, #0b1f16 0%, #0e2a1e 100%); color: #eef6f0; }

    .app-hero {
        display: flex; align-items: center; gap: 18px;
        background: linear-gradient(135deg, #123326 0%, #0b1f16 100%);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 18px;
        padding: 22px 28px;
        margin-bottom: 22px;
        box-shadow: 0 6px 24px rgba(0,0,0,0.25);
    }
    .app-hero-icon {
        font-size: 40px; line-height: 1;
        background: linear-gradient(135deg, #d3a15c, #a97c3c);
        width: 64px; height: 64px; border-radius: 16px;
        display: flex; align-items: center; justify-content: center;
        flex-shrink: 0;
        box-shadow: 0 4px 14px rgba(211,161,92,0.25);
    }
    .app-hero-title { font-size: 26px; font-weight: 800; margin: 0; color: #eef6f0; }
    .app-hero-subtitle { font-size: 14px; color: #93b3a1; margin-top: 2px; }

    .stTabs [data-baseweb="tab-list"] { gap: 6px; background: transparent; justify-content: center; flex-wrap: wrap; }
    .stTabs [data-baseweb="tab"] {
        background: #123326;
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 999px !important;
        padding: 8px 20px;
        color: #93b3a1;
        font-weight: 700;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #4c9a6a 0%, #2f6b48 100%) !important;
        color: white !important;
        border: 1px solid #4c9a6a !important;
    }

    [data-testid="stExpander"] {
        background: #123326;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 14px !important;
        margin-bottom: 10px;
    }

    .stButton > button {
        background: linear-gradient(135deg, #4c9a6a 0%, #2f6b48 100%);
        color: white; border: none; border-radius: 10px; width: 100%;
        font-weight: 700; padding: 10px 0;
        transition: all 0.3s ease;
    }
    .stButton > button:hover { filter: brightness(1.12); transform: translateY(-2px); }
    .stButton > button[kind="primary"] { background: linear-gradient(135deg, #e2665a 0%, #b8443a 100%); }
    .stFormSubmitButton > button {
        background: linear-gradient(135deg, #d3a15c 0%, #a97c3c 100%) !important;
        color: #24170a !important; border: none; border-radius: 10px; font-weight: 800;
        transition: all 0.3s ease;
    }
    .stFormSubmitButton > button:hover { filter: brightness(1.12); transform: translateY(-2px); }

    .stTextInput input, .stNumberInput input, .stDateInput input, .stSelectbox div[data-baseweb="select"] > div {
        background: #0b1f16 !important; border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 10px !important; color: #eef6f0 !important;
    }

    .ear-tag {
        display: inline-flex; align-items: center; gap: 8px;
        background: linear-gradient(135deg, #d3a15c 0%, #a97c3c 100%);
        color: #24170a; font-weight: 800; font-size: 13px;
        padding: 5px 14px 5px 10px; border-radius: 4px 14px 14px 4px; margin: 2px 4px 2px 0;
    }
    .ear-tag::before {
        content: ''; width: 7px; height: 7px; border-radius: 50%;
        background: #0b1f16; border: 2px solid rgba(0,0,0,0.2); flex-shrink: 0;
    }
    .info-chip {
        display: inline-flex; align-items: center; gap: 6px;
        background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.08);
        color: #eef6f0; padding: 4px 12px; border-radius: 999px; font-size: 13px; margin: 2px 4px 2px 0;
    }

    @media (max-width: 768px) {
        .app-hero { flex-direction: column; text-align: center; padding: 16px; }
        .app-hero-icon { width: 50px; height: 50px; font-size: 30px; }
        .app-hero-title { font-size: 20px; }
        .stTabs [data-baseweb="tab"] { padding: 6px 12px; font-size: 12px; }
        [data-testid="column"] { min-width: 100%; }
    }

    .gender-male { background: #4a90d9 !important; }
    .gender-female { background: #e87a7a !important; }
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

if st.session_state.success_msg:
    st.success(st.session_state.success_msg)
    st.session_state.success_msg = None

# ─── دوال مساعدة ──────────────────────────────────────────────────────────

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

def save_image_compressed(uploaded_file, max_size=(800, 800)):
    if uploaded_file is not None:
        try:
            img = Image.open(uploaded_file)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            file_path = f"images/{uuid.uuid4()}.jpg"
            img.save(file_path, "JPEG", quality=85, optimize=True)
            logging.info(f"تم حفظ الصورة: {file_path}")
            return file_path
        except Exception as e:
            logging.error(f"خطأ في حفظ الصورة: {e}")
            return ""
    return ""

def safe_delete_image(path):
    if path and isinstance(path, str) and os.path.exists(path):
        try:
            os.remove(path)
            logging.info(f"تم حذف الصورة: {path}")
        except OSError as e:
            logging.error(f"خطأ في حذف الصورة: {e}")

def load_data(file, columns):
    if not os.path.exists(file):
        logging.info(f"ملف {file} غير موجود، سيتم إنشاؤه")
        return pd.DataFrame(columns=columns)
    try:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            df = pd.DataFrame(data)
            for col in columns:
                if col not in df.columns:
                    if col in ["الأبناء", "اللقاحات", "الجرعات"]:
                        df[col] = "[]"
                    elif col == "وحدة":
                        df[col] = "شهر"
                    else:
                        df[col] = ""
            logging.info(f"تم تحميل {len(df)} سجل من {file}")
            return df
    except Exception as e:
        logging.error(f"خطأ في تحميل {file}: {e}")
        return pd.DataFrame(columns=columns)

def save_data(df, file):
    try:
        df.to_json(file, orient="records", force_ascii=False, indent=4)
        logging.info(f"تم حفظ {len(df)} سجل في {file}")
    except Exception as e:
        logging.error(f"خطأ في حفظ {file}: {e}")
        raise

def auto_backup():
    backup_dir = "backups"
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    date_str = datetime.now().strftime("%Y-%m-%d")
    backup_file = f"{backup_dir}/auto_backup_{date_str}.json"
    if not os.path.exists(backup_file):
        try:
            backup_dict = {
                "herd": st.session_state.herd.to_dict(orient="records"),
                "history": st.session_state.history.to_dict(orient="records"),
                "timestamp": datetime.now().isoformat()
            }
            with open(backup_file, "w", encoding="utf-8") as f:
                json.dump(backup_dict, f, ensure_ascii=False, indent=2)
            logging.info(f"تم إنشاء نسخة احتياطية: {backup_file}")
        except Exception as e:
            logging.error(f"خطأ في النسخ الاحتياطي: {e}")

def validate_sheep_data(data):
    errors = []
    if not data.get("القلادة"):
        errors.append("القلادة مطلوبة")
    if data.get("الجنس") not in ["أنثى", "أنثى صغيرة", "ذكر", "ذكر صغير"]:
        errors.append("الجنس غير صحيح")
    if data.get("العمر", 0) < 0:
        errors.append("العمر لا يمكن أن يكون سالباً")
    if data.get("عدد الولادات", 0) < 0:
        errors.append("عدد الولادات لا يمكن أن يكون سالباً")
    return errors

def refresh_data():
    with st.spinner("جاري تحديث البيانات..."):
        st.session_state.herd = load_data(DATA_FILE, REQUIRED_COLS)
        st.session_state.history = load_data(HISTORY_FILE, HISTORY_COLS)
        time.sleep(0.5)
    st.success("✅ تم تحديث البيانات!")

def check_overdue_vaccinations():
    overdue = []
    for idx, row in st.session_state.herd.iterrows():
        vaccines = safe_literal_eval(row.get("اللقاحات", "[]"))
        if not vaccines:
            overdue.append(row["القلادة"])
    return overdue

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

# ─── تعريف الثوابت ─────────────────────────────────────────────────────────
DATA_FILE = "data/herd_data.json"
HISTORY_FILE = "data/medical_history.json"
REQUIRED_COLS = ["ID", "القلادة", "الجنس", "العمر", "وحدة", "عدد الولادات", "صورة", "اللقاحات", "الجرعات", "آخر تغطيس", "الأم", "الأبناء"]
HISTORY_COLS = ["ID", "التاريخ", "الإجراء", "العلاج", "الأغنام", "صورة"]

# ─── تحميل البيانات ────────────────────────────────────────────────────────
if "herd" not in st.session_state:
    st.session_state.herd = load_data(DATA_FILE, REQUIRED_COLS)
if "history" not in st.session_state:
    st.session_state.history = load_data(HISTORY_FILE, HISTORY_COLS)

auto_backup()

# ─── شريط جانبي ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🛠️ أدوات سريعة")
    if st.button("🔄 تحديث البيانات", use_container_width=True):
        refresh_data()
    st.divider()
    overdue = check_overdue_vaccinations()
    if overdue:
        st.warning(f"⚠️ {len(overdue)} أغنام لم تتلقَّ تطعيمات")
        with st.expander("عرض الأغنام"):
            for name in overdue[:10]:
                st.write(f"- {name}")
    st.divider()
    st.caption(f"📅 آخر تحديث: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# ─── واجهة التطبيق ─────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏠 القطيع", "💉 إجراء طبي", "📋 السجل", "➕ إدارة النظام", "📊 إحصائيات"])

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

        search_col, filter_col = st.columns([2, 1])
        with search_col:
            search_term = st.text_input("🔍 بحث بالقلادة أو المعرف", placeholder="اكتب للبحث...", key="search_sheep")
        with filter_col:
            gender_filter = st.selectbox("تصفية حسب الجنس", ["الكل", "ذكر", "أنثى", "صغار"], key="gender_filter")

        filtered_df = df.copy()
        if search_term:
            filtered_df = filtered_df[filtered_df["القلادة"].str.contains(search_term, case=False, na=False) |
                                      filtered_df["ID"].str.contains(search_term, case=False, na=False)]
        if gender_filter != "الكل":
            if gender_filter == "صغار":
                filtered_df = filtered_df[filtered_df["الجنس"].str.contains("صغير", na=False)]
            else:
                filtered_df = filtered_df[filtered_df["الجنس"] == gender_filter]

        if filtered_df.empty:
            st.info("لا توجد نتائج تطابق معايير البحث")
        else:
            for idx, row in filtered_df.iterrows():
                kids_ids = safe_literal_eval(row.get('الأبناء', '[]'))
                gender_class = "gender-male" if "ذكر" in row['الجنس'] else "gender-female"
                with st.expander(f"🏷️ القلادة: {row['القلادة']} | {row['الجنس']}"):
                    col_img, col_info = st.columns([1, 3])
                    with col_img:
                        if row.get('صورة') and os.path.exists(row['صورة']):
                            st.image(row['صورة'], use_container_width=True)
                    with col_info:
                        st.markdown(f"""
                        <span class="ear-tag {gender_class}">
                            {'♀️' if 'أنثى' in row['الجنس'] else '♂️'} {row['الجنس']}
                        </span>
                        <span class="info-chip">🗓️ {row['العمر']} {row.get('وحدة', 'شهر')}</span>
                        <span class="info-chip">🐑 {row.get('عدد الولادات', 0)} ولادات</span>
                        """, unsafe_allow_html=True)
                        if row.get('الأم'):
                            st.markdown(f"👩 **الأم:** {get_collar_by_id(row['الأم'])}")
                        if kids_ids:
                            k_names = [get_collar_by_id(k) for k in kids_ids if k]
                            if k_names:
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
        if action_type == "تطعيم":
            opts = ['إيفومك', 'معوي/دموي', 'طاعون', 'جدري']
        elif action_type == "جرعة طفيلية":
            opts = ['جرعة كبدية', 'جرعة معوية']
        else:
            opts = ['تغطيس شامل']
        treatment = st.selectbox("العلاج:", opts)
        date = str(st.date_input("التاريخ:"))
        img_file = st.file_uploader("صورة التوثيق (اختياري)", type=['jpg', 'png'])

        if st.button("💾 حفظ الإجراء", use_container_width=True):
            if selected_ids:
                with st.spinner("جاري حفظ الإجراء الطبي..."):
                    new_hist = pd.DataFrame([{
                        "ID": str(uuid.uuid4()),
                        "التاريخ": date,
                        "الإجراء": action_type,
                        "العلاج": treatment,
                        "الأغنام": ", ".join([get_collar_by_id(sid) for sid in selected_ids]),
                        "صورة": save_image_compressed(img_file)
                    }])
                    st.session_state.history = pd.concat([st.session_state.history, new_hist], ignore_index=True)
                    save_data(st.session_state.history, HISTORY_FILE)
                    show_notification("تم تسجيل الإجراء الطبي بنجاح!", "success")
                    time.sleep(0.5)
                    st.rerun()
            else:
                st.warning("الرجاء اختيار رأس واحد على الأقل.")
    else:
        st.warning("يجب إضافة أغنام أولاً.")

# ─── 3. السجل الطبي ───
with tab3:
    st.subheader("📋 السجل الطبي")
    hist_tab1, hist_tab2 = st.tabs(["🔍 عرض السجلات", "✏️ تعديل سجل"])

    with hist_tab1:
        if not st.session_state.history.empty:
            search_hist = st.text_input("🔍 بحث في السجلات", placeholder="ابحث بالإجراء أو العلاج...")
            hist_df = st.session_state.history.copy()
            if search_hist:
                hist_df = hist_df[
                    hist_df["الإجراء"].str.contains(search_hist, case=False, na=False) |
                    hist_df["العلاج"].str.contains(search_hist, case=False, na=False)
                ]
            if hist_df.empty:
                st.info("لا توجد سجلات تطابق البحث")
            else:
                for idx, row in hist_df.iterrows():
                    with st.expander(f"🗓️ {row['التاريخ']} | {row['الإجراء']} ({row['العلاج']})"):
                        st.write(f"**الأغنام المعالجة:** {row['الأغنام']}")
                        if row.get('صورة') and os.path.exists(row['صورة']):
                            st.image(row['صورة'], width=200)
                        if st.button(f"🗑️ حذف السجل", key=f"del_hist_{idx}", type="primary"):
                            with st.spinner("جاري حذف السجل..."):
                                safe_delete_image(row.get('صورة'))
                                st.session_state.history = st.session_state.history.drop(idx).reset_index(drop=True)
                                save_data(st.session_state.history, HISTORY_FILE)
                                show_notification("تم حذف السجل الطبي بنجاح!", "success")
                                time.sleep(0.5)
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
                    st.markdown("### ✏️ تعديل بيانات السجل 
