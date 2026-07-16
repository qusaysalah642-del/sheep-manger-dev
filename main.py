# -*- coding: utf-8 -*-
import os
import sys
import subprocess

# ─── تثبيت المكتبات المطلوبة تلقائياً ──────────────────────────────────
required = ['streamlit', 'pandas', 'Pillow']
for pkg in required:
    try:
        __import__(pkg)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

# ─── الآن الاستيراد ──────────────────────────────────────────────────────
import streamlit as st
import pandas as pd
import json
import uuid
import ast
import time
import logging
from datetime import datetime
from PIL import Image

# ─── إعداد التسجيل ──────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# ─── إعداد الصفحة ──────────────────────────────────────────────────────
st.set_page_config(page_title="Sheep Manager Pro", page_icon="🐑", layout="wide")

# ─── تهيئة Session State ──────────────────────────────────────────────
for key in ["success_msg", "toast"]:
    if key not in st.session_state:
        st.session_state[key] = None

if st.session_state.toast:
    st.toast(st.session_state.toast)
    st.session_state.toast = None

# ─── إنشاء المجلدات تلقائياً ─────────────────────────────────────────
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

def save_image_compressed(uploaded_file, max_size=(800, 800)):
    if uploaded_file is not None:
        try:
            img = Image.open(uploaded_file)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            path = f"images/{uuid.uuid4()}.jpg"
            img.save(path, "JPEG", quality=85, optimize=True)
            return path
        except Exception as e:
            logging.error(f"خطأ في حفظ الصورة: {e}")
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
                    elif col == "وحدة":
                        df[col] = "شهر"
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
    if data.get("العمر", 0) < 0:
        errors.append("العمر لا يمكن أن يكون سالباً")
    if data.get("عدد الولادات", 0) < 0:
        errors.append("عدد الولادات لا يمكن أن يكون سالباً")
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
REQUIRED_COLS = ["ID", "القلادة", "الجنس", "العمر", "وحدة", "عدد الولادات", "صورة", "اللقاحات", "الجرعات", "آخر تغطيس", "الأم", "الأبناء"]
HISTORY_COLS = ["ID", "التاريخ", "الإجراء", "العلاج", "الأغنام", "صورة"]

if "herd" not in st.session_state:
    st.session_state.herd = load_data(DATA_FILE, REQUIRED_COLS)
if "history" not in st.session_state:
    st.session_state.history = load_data(HISTORY_FILE, HISTORY_COLS)

auto_backup()

# ─── CSS مبسط ──────────────────────────────────────────────────────
st.markdown("""
<style>
    body { direction: rtl; }
    .stApp { background: #0b1f16; color: #eef6f0; }
    .stButton > button { background: #4c9a6a; color: white; border-radius: 10px; }
    .stTabs [data-baseweb="tab"] { background: #123326; color: #93b3a1; border-radius: 20px; padding: 8px 16px; }
    .stTabs [aria-selected="true"] { background: #4c9a6a !important; color: white !important; }
    [data-testid="stExpander"] { background: #123326; border-radius: 14px; }
</style>
""", unsafe_allow_html=True)

# ─── الهيدر ──────────────────────────────────────────────────────────
st.markdown("""
<div style="display:flex; align-items:center; gap:15px; background:#123326; padding:20px; border-radius:18px; margin-bottom:20px;">
    <div style="font-size:40px; background:#d3a15c; width:60px; height:60px; border-radius:15px; display:flex; align-items:center; justify-content:center;">🐑</div>
    <div>
        <h1 style="margin:0; color:white;">Sheep Manager Pro</h1>
        <p style="margin:0; color:#93b3a1;">إدارة القطيع، التطعيمات، والسجل الطبي</p>
    </div>
</div>
""", unsafe_allow_html=True)

if st.session_state.success_msg:
    st.success(st.session_state.success_msg)
    st.session_state.success_msg = None

# ─── الأقسام الرئيسية ──────────────────────────────────────────────
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

        search_term = st.text_input("🔍 بحث", placeholder="ابحث بالقلادة...")
        filtered_df = df.copy()
        if search_term:
            filtered_df = filtered_df[filtered_df["القلادة"].str.contains(search_term, case=False, na=False)]

        for _, row in filtered_df.iterrows():
            with st.expander(f"🏷️ {row['القلادة']} - {row['الجنس']}"):
                if row.get('صورة') and os.path.exists(row['صورة']):
                    st.image(row['صورة'], width=150)
                st.write(f"**العمر:** {row['العمر']} {row.get('وحدة', 'شهر')}")
                st.write(f"**عدد الولادات:** {row.get('عدد الولادات', 0)}")
                if row.get('الأم'):
                    st.write(f"**الأم:** {get_collar_by_id(row['الأم'])}")
    else:
        st.info("القطيع فارغ.")

# ─── 2. إجراء طبي ───
with tab2:
    st.subheader("💉 تسجيل إجراء طبي")
    if not st.session_state.herd.empty:
        herd_ids = st.session_state.herd["ID"].tolist()
        selected = st.multiselect("اختر الأغنام:", herd_ids, format_func=format_sheep_label)
        action = st.radio("النوع:", ["تطعيم", "جرعة طفيلية", "تغطيس"], horizontal=True)
        opts = {'تطعيم': ['إيفومك', 'معوي/دموي', 'طاعون', 'جدري'],
                'جرعة طفيلية': ['جرعة كبدية', 'جرعة معوية'],
                'تغطيس': ['تغطيس شامل']}
        treatment = st.selectbox("العلاج:", opts[action])
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
        for idx, row in st.session_state.history.iterrows():
            with st.expander(f"🗓️ {row['التاريخ']} - {row['الإجراء']} ({row['العلاج']})"):
                st.write(f"**الأغنام:** {row['الأغنام']}")
                if row.get('صورة') and os.path.exists(row['صورة']):
                    st.image(row['صورة'], width=150)
                if st.button(f"🗑️ حذف", key=f"del_{idx}", type="primary"):
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
            age = st.number_input("العمر", min_value=0)
            unit = st.selectbox("الوحدة", ["شهر", "سنة"])
            births = st.number_input("عدد الولادات", min_value=0)
            mother = st.selectbox("الأم", [None]+st.session_state.herd["ID"].tolist(),
                                  format_func=lambda x: "بدون" if x is None else format_sheep_label(x))
            img = st.file_uploader("صورة", type=['jpg','png'])
            if st.form_submit_button("➕ إضافة"):
                if collar:
                    data = {"القلادة":collar, "الجنس":gender, "العمر":age, "عدد الولادات":births}
                    errors = validate_sheep_data(data)
                    if errors:
                        for e in errors: st.error(f"❌ {e}")
                    else:
                        new_id = str(uuid.uuid4())
                        new_row = pd.DataFrame([{
                            "ID": new_id, "القلادة": collar, "الجنس": gender,
                            "العمر": age, "وحدة": unit, "عدد الولادات": births,
                            "الأم": mother or "", "الأبناء": "[]",
                            "صورة": save_image_compressed(img),
                            "اللقاحات": "[]", "الجرعات": "[]", "آخر تغطيس": ""
                        }])
                        st.session_state.herd = pd.concat([st.session_state.herd, new_row], ignore_index=True)
                        if mother:
                            m_idx = st.session_state.herd[st.session_state.herd["ID"]==mother].index[0]
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
                idx = st.session_state.herd[st.session_state.herd["ID"]==target].index[0]
                row = st.session_state.herd.iloc[idx]
                with st.form("edit"):
                    new_collar = st.text_input("القلادة*", value=row["القلادة"])
                    new_gender = st.selectbox("الجنس*", ["أنثى","أنثى صغيرة","ذكر","ذكر صغير"], index=["أنثى","أنثى صغيرة","ذكر","ذكر صغير"].index(row["الجنس"]))
                    new_age = st.number_input("العمر", min_value=0, value=int(row["العمر"]))
                    new_unit = st.selectbox("الوحدة", ["شهر","سنة"], index=["شهر","سنة"].index(row.get("وحدة","شهر")))
                    new_births = st.number_input("عدد الولادات", min_value=0, value=int(row["عدد الولادات"]))
                    new_mother = st.selectbox("الأم", [None]+st.session_state.herd["ID"].tolist(),
                                              index=([None]+st.session_state.herd["ID"].tolist()).index(row.get("الأم")) if row.get("الأم") in [None]+st.session_state.herd["ID"].tolist() else 0,
                                              format_func=lambda x: "بدون" if x is None else format_sheep_label(x))
                    new_img = st.file_uploader("تحديث الصورة", type=['jpg','png'])
                    if st.form_submit_button("💾 حفظ"):
                        st.session_state.herd.at[idx, "القلادة"] = new_collar
                        st.session_state.herd.at[idx, "الجنس"] = new_gender
                        st.session_state.herd.at[idx, "العمر"] = new_age
                        st.session_state.herd.at[idx, "وحدة"] = new_unit
                        st.session_state.herd.at[idx, "عدد الولادات"] = new_births
                        st.session_state.herd.at[idx, "الأم"] = new_mother or ""
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
                           data=json.dumps({"herd":st.session_state.herd.to_dict(orient="records"),
                                            "history":st.session_state.history.to_dict(orient="records")},
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

# ─── 5. إحصائيات ───
with tab5:
    st.subheader("📊 إحصائيات متقدمة")
    if not st.session_state.herd.empty:
        df = st.session_state.herd
        st.bar_chart(df["العمر"].value_counts().sort_index())
        st.dataframe(df[["القلادة","الجنس","العمر","عدد الولادات"]])
    else:
        st.info("لا توجد بيانات")
