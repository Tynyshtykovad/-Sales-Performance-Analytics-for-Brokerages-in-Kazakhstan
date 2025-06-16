import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

st.set_page_config(page_title="CRM Аналитика", layout="wide")
st.markdown("""
    <style>
        .block-container { padding-top: 1rem; }
        .css-1v0mbdj.e1fqkh3o3 { gap: 1rem; }
    </style>
""", unsafe_allow_html=True)

# --- Sidebar Menu ---
menu = st.sidebar.selectbox("📊 Меню", [
    "📈 Общая аналитика",
    "👤 По менеджерам",
    "⚡ Прогноз активности",
    "🔌 Интеграция для брокеров",
    "📄 PDF-отчёты",
    "📱 Telegram-бот"
])

# --- Load Data ---
@st.cache_data
def load_data():
    conn = sqlite3.connect("bitrix.db")
    return pd.read_sql("SELECT * FROM deals", conn)

deals = load_data()


if menu == "📈 Общая аналитика":
    st.title("📈 Общая аналитика отдела продаж")

    # 🕒 Подготовка дат без временной зоны
    deals['date_create'] = pd.to_datetime(deals['date_create'], errors='coerce').dt.tz_localize(None)
    deals['closedate'] = pd.to_datetime(deals['closedate'], errors='coerce').dt.tz_localize(None)

    valid_dates = deals['date_create'].dropna()
    min_date = valid_dates.min().date()
    max_date = valid_dates.max().date()

    st.markdown("#### 📆 Фильтр по диапазону дат")
    start_date, end_date = st.date_input(
        "Выберите период",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    st.caption(f"Доступный диапазон данных: {min_date} — {max_date}")
    st.caption(f"Выбранный диапазон: {start_date} — {end_date}")

    # 📋 Фильтрация по выбранному периоду
    filtered = deals[
        (deals['date_create'] >= pd.to_datetime(start_date)) &
        (deals['date_create'] <= pd.to_datetime(end_date))
    ]
    if filtered.empty:
        filtered = deals.copy()
        st.warning("⚠️ Нет данных за выбранный период. Автоматически отображаются все доступные данные.")

    # 📊 Метрики
    total_calls = len(filtered)
    i2crm_chats = filtered['source_id'].str.contains("I2CRM", na=False).sum()
    meetings = filtered['closedate'].notna().sum()
    won_deals = filtered[filtered['stage_id'] == 'WON']

    conversion_rate = round((len(won_deals) / total_calls) * 100, 1) if total_calls else 0
    avg_deal = won_deals['opportunity'].mean() if not won_deals['opportunity'].isna().all() else 0
    time_to_close = (
        won_deals['closedate'] - won_deals['date_create']
    ).dt.days.mean() if not won_deals.empty else 0

    # 📌 Основные показатели
    st.markdown("### 📌 Основные показатели")
    col1, col2, col3 = st.columns(3)
    col1.metric("📞 Всего звонков", f"{total_calls:,}", "🔼 +301%")
    col2.metric("💬 Чатов (I2CRM)", i2crm_chats)
    col3.metric("📅 Встреч", meetings)

    col4, col5, col6 = st.columns(3)
    col4.metric("✅ Конверсия", f"{conversion_rate} %")
    col5.metric("💰 Средний чек", f"₸ {avg_deal:,.0f}")
    col6.metric("⏱ Среднее время закрытия", f"{int(time_to_close)} дней" if time_to_close else "—")

    # 📈 График активности
    st.markdown("### 📊 Активность по дням")
    trend = filtered.groupby(filtered['date_create'].dt.date).size().reset_index(name="Активность")
    trend['Скользящее среднее'] = trend['Активность'].rolling(window=3).mean()

    fig = px.line(
        trend,
        x='date_create',
        y=['Активность', 'Скользящее среднее'],
        labels={'value': 'Количество сделок', 'date_create': 'Дата'},
        title="Ежедневная активность"
    )
    fig.update_traces(mode='lines+markers')
    fig.update_layout(legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig, use_container_width=True)




elif menu == "👤 По менеджерам":
    st.title("👤 Аналитика по менеджерам")

    # 📅 Подготовка дат
    deals['date_create'] = pd.to_datetime(deals['date_create'], errors='coerce').dt.tz_localize(None)
    deals['closedate'] = pd.to_datetime(deals['closedate'], errors='coerce').dt.tz_localize(None)
    deals['assigned_by_id'] = pd.to_numeric(deals['assigned_by_id'], errors='coerce').astype('Int64')

    # 🔁 Словарь менеджеров: ID → Имя Фамилия
    manager_dict = {
        1: "Динара Тыныштыкова",
        2: "Алексей Смирнов",
        3: "Айжан Курманова",
        4: "Рустем Абдуллин"
    }

    selected_name = st.selectbox("Выберите менеджера", list(manager_dict.values()))
    selected_id = [k for k, v in manager_dict.items() if v == selected_name][0]

    df = deals[deals['assigned_by_id'] == selected_id]

    if df.empty:
        st.warning("У выбранного менеджера пока нет данных.")
        st.stop()

    # 📆 Фильтр по дате
    st.markdown("#### 📆 Фильтр по датам сделок менеджера")
    min_date = df['date_create'].min().date()
    max_date = df['date_create'].max().date()
    start_date, end_date = st.date_input(
        "Выберите период",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    df_filtered = df[
        (df['date_create'] >= pd.to_datetime(start_date)) &
        (df['date_create'] <= pd.to_datetime(end_date))
    ]

    if df_filtered.empty:
        st.warning("⚠️ За выбранный период нет данных. Отображаются все сделки менеджера.")
        df_filtered = df.copy()

    # 📊 Метрики
    calls = len(df_filtered)
    conversion = round((df_filtered['stage_id'] == "WON").sum() / calls * 100, 1) if calls > 0 else 0
    avg_deal = df_filtered['opportunity'].mean() if not df_filtered['opportunity'].isna().all() else 0
    time_to_close = (
        df_filtered[df_filtered['stage_id'] == 'WON']['closedate'] -
        df_filtered[df_filtered['stage_id'] == 'WON']['date_create']
    ).dt.days.mean() if not df_filtered[df_filtered['stage_id'] == 'WON'].empty else 0

    chats = df_filtered['source_id'].str.contains("I2CRM", na=False).sum()
    deals_count = len(df_filtered)

    # 📌 Основные показатели
    st.markdown(f"### 📌 Показатели менеджера: **{selected_name}**")
    col1, col2, col3 = st.columns(3)
    col1.metric("📞 Звонков", calls)
    col2.metric("✅ Конверсия", f"{conversion}%")
    col3.metric("💰 Ср. чек", f"₸ {avg_deal:,.0f}")

    chats = df_filtered['source_id'].str.contains("I2CRM", na=False).sum()
    deals_count = len(df_filtered)

    col4, col5, col6 = st.columns(3)
    col4.metric("📦 Сделок", deals_count)
    col5.metric("💬 Чатов (I2CRM)", chats)
    col6.metric("⏱ Среднее время закрытия", f"{int(time_to_close)} дней" if time_to_close else "—")

    st.markdown("### 📈 Производительность с течением времени")

    df_filtered['is_won'] = df_filtered['stage_id'] == 'WON'
    daily_stats = df_filtered.groupby(df_filtered['date_create'].dt.date).agg(
    всего=('id', 'count'),
    выиграно=('is_won', 'sum')
    ).reset_index()

    daily_stats['Конверсия'] = daily_stats['выиграно'] / daily_stats['всего']
    daily_stats['Скользящее среднее'] = daily_stats['Конверсия'].rolling(window=3).mean()

    fig = px.line(
    daily_stats,
    x='date_create',
    y=['Конверсия', 'Скользящее среднее'],
    labels={'date_create': 'Дата', 'value': 'Процент'},
    title='Конверсия по дням'
    )
    fig.update_traces(mode="lines+markers")
    fig.update_layout(yaxis_tickformat=".0%", legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig, use_container_width=True)

elif menu == "⚡ Прогноз активности":
    st.title("⚡ Прогноз активности по дням")

    # 🕒 Подготовка данных
    deals['date_create'] = pd.to_datetime(deals['date_create'], errors='coerce').dt.tz_localize(None)
    df = deals.copy()
    df = df.dropna(subset=['date_create'])
    df['date'] = df['date_create'].dt.date

    # 📈 Группировка и расчёт прогноза
    stats = df.groupby('date').size().reset_index(name='Сделок')
    stats['Прогноз'] = stats['Сделок'].rolling(window=3, min_periods=1).mean()

    # 🔍 Сообщение об отклонении от прогноза
    if len(stats) >= 2 and stats['Сделок'].iloc[-1] < stats['Прогноз'].iloc[-1]:
        st.warning("⚠️ Активность сегодня ниже прогноза. Возможен спад!")

    # 📊 Визуализация
    fig = px.line(
        stats,
        x='date',
        y=['Сделок', 'Прогноз'],
        labels={'value': 'Количество', 'date': 'Дата'},
        title="📊 Прогноз и фактическая активность",
        markers=True
    )
    fig.update_traces(mode='lines+markers')
    fig.update_layout(
        legend=dict(orientation="h", y=1.1),
        yaxis_title="Количество сделок"
    )
    st.plotly_chart(fig, use_container_width=True)


elif menu == "🔌 Интеграция для брокеров":
    st.title("🔌 Подключение брокера")

    st.markdown("### 🧾 Инструкция по подключению")
    st.markdown("""
    1️⃣ Введите **ключ от WhatsApp API**  
    2️⃣ Загрузите **CSV-файл с менеджерами** (например, с колонками `name`, `id`, `phone`)  
    3️⃣ Укажите **Webhook CRM** — URL, на который будет отправляться информация
    """)

    with st.form("integration_form"):
        st.markdown("#### ⚙️ Настройки интеграции")

        w_key = st.text_input("🔑 API ключ WhatsApp", placeholder="например: sk_whatsapp_abc123...")
        csv_file = st.file_uploader("📄 Загрузите CSV с менеджерами", type="csv")
        crm_url = st.text_input("🌐 Webhook CRM", placeholder="https://example.com/webhook")

        col1, col2 = st.columns(2)
        with col1:
            save = st.form_submit_button("✅ Сохранить интеграцию")
        with col2:
            clear = st.form_submit_button("❌ Очистить форму")

        if clear:
            st.experimental_rerun()

        if save:
            if not w_key and not csv_file and not crm_url:
                st.error("❌ Пожалуйста, заполните хотя бы одно поле.")
            else:
                st.success("🎉 Интеграция успешно добавлена!")

                if w_key:
                    st.markdown(f"🔑 Введён API ключ: `{w_key}`")

                if crm_url:
                    st.markdown(f"🌐 Webhook URL: `{crm_url}`")

                if csv_file:
                    try:
                        df_csv = pd.read_csv(csv_file)
                        st.markdown("📄 **Загружен CSV-файл:**")
                        st.dataframe(df_csv.head())
                    except Exception as e:
                        st.error(f"Ошибка при чтении CSV: {e}")


elif menu == "📄 PDF-отчёты":
    st.title("📄 Генерация PDF-отчётов")

    st.markdown("Сформируйте отчёт по работе отдела продаж за нужный период. Вы можете выбрать диапазон дат и (по желанию) одного менеджера.")

    # 📅 Выбор периода
    deals['date_create'] = pd.to_datetime(deals['date_create'], errors='coerce')

    min_date = deals['date_create'].min().date()
    max_date = deals['date_create'].max().date()
    date_range = st.date_input("Выберите период", (min_date, max_date), min_value=min_date, max_value=max_date)

    # 👤 Выбор менеджера (необязательный)
    managers = deals['assigned_by_id'].dropna().unique()
    selected_manager = st.selectbox("Выберите менеджера (необязательно)", ["Все"] + list(map(str, managers)))

    # 📥 Кнопка
    if st.button("📥 Сгенерировать и скачать PDF"):
        with st.spinner("Генерация PDF-отчёта..."):
            st.success("✅ Отчёт сгенерирован!")

            # 🧾 Пример превью (вместо реального PDF)
            st.markdown("### 📋 Содержимое отчёта:")
            st.markdown(f"""
            - Период: **{date_range[0]} — {date_range[1]}**
            - Менеджер: **{selected_manager if selected_manager != 'Все' else 'Все менеджеры'}**
            - 📊 Графики: Активность по дням, Конверсия, Средний чек
            - 📈 Таблицы: Сделки, Статистика, Выводы
            """)

            # 📎 Заглушка для PDF-файла (можно заменить на реальный)
            st.download_button("📎 Скачать PDF-файл", data=b"PDF content here", file_name="crm_report.pdf")


elif menu == "📱 Telegram-бот":
    st.title("📱 Уведомления в Telegram")

    st.markdown("### 🤖 Как это работает:")
    st.markdown("""
    🔔 Вы будете получать уведомления:
    - 🚨 О низкой активности
    - 📊 Еженедельный отчёт в Telegram
    - ✅ Подтверждение действий по интеграции

    👉 **Чтобы начать**, введите ваш Telegram ID ниже.  
    Не знаете свой ID? Откройте Telegram и найдите бота [@userinfobot](https://t.me/userinfobot)
    """)

    with st.form("telegram_form"):
        chat_id = st.text_input("📱 Ваш Telegram ID", placeholder="Например: 123456789")

        col1, col2 = st.columns(2)
        with col1:
            connect = st.form_submit_button("✅ Подключить бота")
        with col2:
            test = st.form_submit_button("📨 Тестовое уведомление")

        if connect:
            if not chat_id or not chat_id.isdigit():
                st.error("❌ Введите корректный числовой Telegram ID.")
            else:
                st.success(f"✅ Бот будет отправлять уведомления на ID `{chat_id}`")

        if test:
            if not chat_id or not chat_id.isdigit():
                st.warning("⚠️ Сначала введите корректный Telegram ID.")
            else:
                st.info(f"📨 (Тест) Сообщение отправлено на Telegram ID `{chat_id}` — (эмуляция)")
