from telegram import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)


# ─── Foydalanuvchi klaviaturasi ──────────────────────────────────────────────

def user_keyboard() -> ReplyKeyboardMarkup:
    layout = [
        ["📚 Kurs haqida ma'lumot", "💰 Kurs narxi"],
        ["👤 Profil",               "📞 Admin bilan bog'lanish"],
    ]
    return ReplyKeyboardMarkup(layout, resize_keyboard=True)


# ─── Admin klaviaturasi ──────────────────────────────────────────────────────

def admin_keyboard() -> ReplyKeyboardMarkup:
    layout = [
        ["📚 Kurs haqida ma'lumot", "💰 Kurs narxi"],
        ["📢 Xabar yuborish",        "👨‍🎓 O'quvchilar"],
        ["👤 Profil"],
    ]
    return ReplyKeyboardMarkup(layout, resize_keyboard=True)


# ─── Telefon so'rash ─────────────────────────────────────────────────────────

def phone_keyboard() -> ReplyKeyboardMarkup:
    layout = [[KeyboardButton("📱 Telefon raqamni yuborish", request_contact=True)]]
    return ReplyKeyboardMarkup(layout, resize_keyboard=True, one_time_keyboard=True)


# ─── Bekor qilish ────────────────────────────────────────────────────────────

def cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup([["/cancel"]], resize_keyboard=True)


# ─── Kursga qo'shilish (foydalanuvchi — "Admin bilan bog'lanish") ────────────

def join_course_keyboard(admin_username: str) -> InlineKeyboardMarkup:
    buttons = [[
        InlineKeyboardButton("✅ Kursga qo'shilish", url=f"https://t.me/{admin_username}")
    ]]
    return InlineKeyboardMarkup(buttons)


# ─── Broadcast tasdiqlash (admin) ────────────────────────────────────────────

def broadcast_confirm_keyboard() -> InlineKeyboardMarkup:
    buttons = [[
        InlineKeyboardButton("✅ Yuborish",       callback_data="broadcast_send"),
        InlineKeyboardButton("❌ Bekor qilish",   callback_data="broadcast_cancel"),
    ]]
    return InlineKeyboardMarkup(buttons)


# ─── O'quvchi kartasi (admin — O'quvchilar bo'limi) ──────────────────────────

def student_card_keyboard(telegram_id: int) -> InlineKeyboardMarkup:
    buttons = [[
        InlineKeyboardButton("✅ Bog'lanib bo'ldim", callback_data=f"connected_{telegram_id}")
    ]]
    return InlineKeyboardMarkup(buttons)
