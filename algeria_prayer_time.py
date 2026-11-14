import datetime
import pandas as pd
import requests
import streamlit as st
# 1. إعدادات الصفحة الأساسية (يجب أن يكون أول أمر Streamlit في الملف)
st.set_page_config(
    page_title="مواقيت الصلاة في الجزائر",
    page_icon="🕌",
    layout="wide",
    initial_sidebar_state="collapsed",
)
# 2. تنسيقات CSS متقدمة: خط Cairo، اتجاه RTL، شبكة متجاوبة، وأنيميشن سلس
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');
    [data-testid="stMainBlockContainer"],
    [data-testid="stSidebarContent"] {
        direction: rtl;
        text-align: right;
        font-family: 'Cairo', sans-serif;
    }
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }
    /* أنيميشن ظهور البطاقات بتدرج ناعم */
    @keyframes fadeSlideUp {
        from {
            opacity: 0;
            transform: translateY(18px) scale(0.97);
        }
        to {
            opacity: 1;
            transform: translateY(0) scale(1);
        }
    }
    /* أنيميشن نبض لطيف لبطاقة الصلاة القادمة */
    @keyframes pulseGlow {
        0% {
            box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.45);
        }
        70% {
            box-shadow: 0 0 0 12px rgba(16, 185, 129, 0);
        }
        100% {
            box-shadow: 0 0 0 0 rgba(16, 185, 129, 0);
        }
    }
    /* بطاقة الترحيب والعد التنازلي للصلاة القادمة */
    .hero-banner {
        background: linear-gradient(135deg, #064e3b 0%, #0f766e 60%, #115e59 100%);
        border: 1px solid rgba(52, 211, 153, 0.35);
        border-radius: 18px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 1.25rem;
        color: #ffffff;
        box-shadow: 0 10px 28px rgba(0, 0, 0, 0.25);
        animation: fadeSlideUp 0.5s ease-out both;
    }
    .hero-title {
        font-size: 1.65rem;
        font-weight: 800;
        margin: 0 0 0.35rem 0;
    }
    .hero-sub {
        font-size: 0.95rem;
        color: #d1fae5;
        margin: 0;
    }
    .next-badge {
        display: inline-block;
        margin-top: 0.75rem;
        background: rgba(255, 255, 255, 0.14);
        border: 1px solid rgba(255, 255, 255, 0.25);
        padding: 0.35rem 0.85rem;
        border-radius: 999px;
        font-size: 0.92rem;
        font-weight: 700;
    }
    /* شبكة البطاقات المتجاوبة: عمودان على الهاتف و6 أعمدة على الشاشات الكبيرة */
    .prayers-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
        gap: 14px;
        margin-top: 0.75rem;
        margin-bottom: 1.5rem;
    }
    .prayer-card {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 16px;
        padding: 1rem 0.75rem;
        text-align: center;
        transition: transform 0.25s ease, border-color 0.25s ease, background 0.25s ease;
        animation: fadeSlideUp 0.55s ease-out both;
    }
    .prayer-card:hover {
        transform: translateY(-4px);
        border-color: rgba(52, 211, 153, 0.6);
        background: rgba(16, 185, 129, 0.08);
    }
    .prayer-card.active {
        background: linear-gradient(160deg, rgba(16, 185, 129, 0.22), rgba(6, 78, 59, 0.45));
        border: 1.5px solid #10b981;
        animation: fadeSlideUp 0.55s ease-out both, pulseGlow 2.4s infinite;
    }
    .prayer-icon {
        font-size: 1.5rem;
        margin-bottom: 0.25rem;
    }
    .prayer-name {
        font-size: 1rem;
        font-weight: 700;
        color: #e5e7eb;
        margin-bottom: 0.25rem;
    }
    .prayer-time {
        font-size: 1.65rem;
        font-weight: 800;
        color: #34d399;
        letter-spacing: 0.5px;
    }
    .active-tag {
        display: inline-block;
        margin-top: 0.35rem;
        font-size: 0.72rem;
        font-weight: 700;
        color: #064e3b;
        background: #34d399;
        padding: 2px 8px;
        border-radius: 999px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
# 3. قاموس الولايات الجزائرية (الاسم بالعربية -> الاسم المطلوب في API)
ALGERIA_CITIES = {
    "قسنطينة": "Constantine",
    "برج بوعريريج": "Bordj Bou Arreridj",
    "الجزائر العاصمة": "Algiers",
    "وهران": "Oran",
    "سطيف": "Setif",
    "عنابة": "Annaba",
    "باتنة": "Batna",
    "بجاية": "Bejaia",
    "جيجل": "Jijel",
    "سكيكدة": "Skikda",
    "ميلة": "Mila",
    "أم البواقي": "Oum El Bouaghi",
    "خنشلة": "Khenchela",
    "قالمة": "Guelma",
    "سوق أهراس": "Souk Ahras",
    "تبسة": "Tebessa",
    "بسكرة": "Biskra",
    "تلمسان": "Tlemcen",
    "ورقلة": "Ouargla",
    "غرداية": "Ghardaia",
    "تمنراست": "Tamanrasset",
    "أدرار": "Adrar",
}
PRAYER_META = [
    ("Fajr", "الفجر", "🌙"),
    ("Sunrise", "الشروق", "🌅"),
    ("Dhuhr", "الظهر", "☀️"),
    ("Asr", "العصر", "🌤️"),
    ("Maghrib", "المغرب", "🌇"),
    ("Isha", "العشاء", "🌃"),
]
# 4. دالة جلب المواقيت من AlAdhan API مع التخزين المؤقت لمدة ساعة
@st.cache_data(ttl=3600)
def fetch_prayer_times(city_en: str, selected_date: datetime.date):
    date_str = selected_date.strftime("%d-%m-%Y")
    url = f"https://api.aladhan.com/v1/timingsByCity/{date_str}"
    params = {
        "city": city_en,
        "country": "Algeria",
        "method": 19,  # طريقة الحساب الجزائرية الرسمية
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        payload = response.json()
        if payload.get("code") == 200:
            return payload["data"], None
        return None, "تعذر جلب البيانات من الخادم."
    except requests.RequestException as err:
        return None, f"خطأ في الاتصال بالإنترنت: {err}"
# 5. دالة لحساب الصلاة القادمة والوقت المتبقي لها (توقيت الجزائر UTC+1)
def get_next_prayer(timings: dict, selected_date: datetime.date):
    dz_tz = datetime.timezone(datetime.timedelta(hours=1))
    now_dz = datetime.datetime.now(dz_tz)
    if selected_date != now_dz.date():
        return None, None
    for key_en, name_ar, _ in PRAYER_META:
        if key_en == "Sunrise":
            continue
        hh, mm = map(int, timings[key_en].split(" ")[0].split(":"))
        prayer_dt = datetime.datetime.combine(
            selected_date, datetime.time(hh, mm), tzinfo=dz_tz
        )
        if prayer_dt > now_dz:
            diff = prayer_dt - now_dz
            hours, rem = divmod(int(diff.total_seconds()), 3600)
            mins = rem // 60
            return key_en, f"متبقي على صلاة {name_ar}: {hours} س و {mins} د"
    return "Fajr", "انتهت صلوات اليوم — الصلاة القادمة هي الفجر"
# 6. أدوات الاختيار في أعلى الصفحة (متوافقة تمامًا مع الهاتف)
col1, col2 = st.columns(2)
with col1:
    selected_wilaya = st.selectbox("📍 اختر الولاية:", list(ALGERIA_CITIES.keys()))
with col2:
    selected_date = st.date_input("📅 اختر التاريخ:", value=datetime.date.today())
# 7. جلب وعرض المواقيت
city_en = ALGERIA_CITIES[selected_wilaya]
with st.spinner("جاري تحديث المواقيت..."):
    data, error = fetch_prayer_times(city_en, selected_date)
if error:
    st.error(error)
elif data:
    timings = data["timings"]
    hijri = data["date"]["hijri"]
    hijri_text = f"{hijri['day']} {hijri['month']['ar']} {hijri['year']} هـ"
    next_key, countdown_text = get_next_prayer(timings, selected_date)
    badge_html = (
        f'<div class="next-badge">⏳ {countdown_text}</div>'
        if countdown_text
        else ""
    )
    st.markdown(
        f"""
        <div class="hero-banner">
            <div class="hero-title">🕌 مواقيت الصلاة — {selected_wilaya}</div>
            <p class="hero-sub">{selected_date.strftime('%Y-%m-%d')} &nbsp;|&nbsp; {hijri_text}</p>
            {badge_html}
        </div>
        """,
        unsafe_allow_html=True,
    )
    # بناء بطاقات الصلوات مع تأخير أنيميشن متدرج لكل بطاقة
    cards_html = '<div class="prayers-grid">'
    for idx, (key_en, name_ar, icon) in enumerate(PRAYER_META):
        clean_time = timings[key_en].split(" ")[0]
        is_next = key_en == next_key
        active_cls = " active" if is_next else ""
        active_tag = '<div class="active-tag">القادمة</div>' if is_next else ""
        delay = idx * 0.07
        cards_html += (
            f'<div class="prayer-card{active_cls}" style="animation-delay: {delay:.2f}s;">'
            f'<div class="prayer-icon">{icon}</div>'
            f'<div class="prayer-name">{name_ar}</div>'
            f'<div class="prayer-time">{clean_time}</div>'
            f'{active_tag}'
            f'</div>'
        )
    cards_html += "</div>"
    st.markdown(cards_html, unsafe_allow_html=True)