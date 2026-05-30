import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

import database as db
import buttons
from config import ADMIN_ID, ADMIN_USERNAME, BOT_TOKEN

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)

# ─── Suhbat holatlari ────────────────────────────────────────────────────────

(
    REGISTER_NAME,
    REGISTER_PHONE,
    MAIN_MENU,
    ADMIN_COURSE_INFO,
    ADMIN_COURSE_PRICE,
    ADMIN_BROADCAST,
    ADMIN_BROADCAST_CONFIRM,
) = range(7)


# ─── Yordamchi funksiyalar ───────────────────────────────────────────────────

def extract_content(message):
    """Xabardan (content_type, file_id, caption) qaytaradi."""
    if message.photo:
        return "photo", message.photo[-1].file_id, message.caption or ""
    if message.video:
        return "video", message.video.file_id, message.caption or ""
    if message.document:
        return "document", message.document.file_id, message.caption or ""
    if message.audio:
        return "audio", message.audio.file_id, message.caption or ""
    if message.voice:
        return "voice", message.voice.file_id, message.caption or ""
    return "text", message.text or "", ""


async def send_stored(bot, chat_id: int, row: tuple):
    """Ma'lumotlar bazasidan olingan qatorni yuboradi."""
    _, content_type, file_id, caption = row
    if content_type == "text":
        await bot.send_message(chat_id, file_id)
    elif content_type == "photo":
        await bot.send_photo(chat_id, file_id, caption=caption or None)
    elif content_type == "video":
        await bot.send_video(chat_id, file_id, caption=caption or None)
    elif content_type == "document":
        await bot.send_document(chat_id, file_id, caption=caption or None)
    elif content_type == "audio":
        await bot.send_audio(chat_id, file_id, caption=caption or None)
    elif content_type == "voice":
        await bot.send_voice(chat_id, file_id, caption=caption or None)


async def forward_to(bot, msg, chat_id: int):
    """Saqlangan broadcast xabarini boshqa foydalanuvchiga yuboradi."""
    content_type, file_id, caption = extract_content(msg)
    await send_stored(bot, chat_id, (None, content_type, file_id, caption))


def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


# ─── /myid ───────────────────────────────────────────────────────────────────

async def cmd_myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    await update.message.reply_text(f"Sizning Telegram ID: <code>{uid}</code>", parse_mode="HTML")


# ─── /start ──────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    logging.info(f"/start bosdi: user_id={uid}, config ADMIN_ID={ADMIN_ID}, admin={is_admin(uid)}")

    # Admin ro'yxatdan o'tmagan bo'lsa ham to'g'ridan-to'g'ri admin panelga
    if is_admin(uid):
        user = db.get_user(uid)
        if not user:
            db.add_user(uid, "Admin", "—", update.effective_user.username or "")
        await update.message.reply_text(
            "Salom, Admin! 👋\n\nAdmin panel:",
            reply_markup=buttons.admin_keyboard(),
        )
        return MAIN_MENU

    user = db.get_user(uid)
    if user and user[6]:  # is_active
        await update.message.reply_text(f"Xush kelibsiz, {user[2]}! 👋", reply_markup=buttons.user_keyboard())
        return MAIN_MENU

    await update.message.reply_text(
        "Assalomu alaykum! Botga xush kelibsiz. 👋\n\n"
        "Ro'yxatdan o'tish uchun <b>Ism va Familiyangizni</b> kiriting:",
        parse_mode="HTML",
    )
    return REGISTER_NAME


# ─── Ro'yxatdan o'tish ───────────────────────────────────────────────────────

async def register_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["full_name"] = update.message.text.strip()
    await update.message.reply_text(
        "Telefon raqamingizni yuboring:",
        reply_markup=buttons.phone_keyboard(),
    )
    return REGISTER_PHONE


async def register_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.contact:
        phone = update.message.contact.phone_number
    else:
        phone = update.message.text.strip()

    tg_user = update.effective_user
    full_name = context.user_data.get("full_name", tg_user.full_name)
    db.add_user(tg_user.id, full_name, phone, tg_user.username or "")

    kb = buttons.admin_keyboard() if is_admin(tg_user.id) else buttons.user_keyboard()
    await update.message.reply_text(
        f"✅ Ro'yxatdan muvaffaqiyatli o'tdingiz!\n\nXush kelibsiz, <b>{full_name}</b>!",
        parse_mode="HTML",
        reply_markup=kb,
    )
    return MAIN_MENU


# ─── Foydalanuvchi — Kurs haqida ma'lumot ────────────────────────────────────

async def user_course_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = db.get_course_info()
    if not rows:
        await update.message.reply_text("Hozircha kurs haqida ma'lumot yo'q.")
        return MAIN_MENU
    for row in rows:
        await send_stored(context.bot, update.effective_chat.id, row)
    return MAIN_MENU


# ─── Foydalanuvchi — Kurs narxi ──────────────────────────────────────────────

async def user_course_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = db.get_course_price()
    if not rows:
        await update.message.reply_text("Hozircha kurs narxi kiritilmagan.")
        return MAIN_MENU
    for row in rows:
        await send_stored(context.bot, update.effective_chat.id, row)
    return MAIN_MENU


# ─── Foydalanuvchi — Profil ───────────────────────────────────────────────────

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = db.get_user(update.effective_user.id)
    if not user:
        await update.message.reply_text("Profil topilmadi. /start buyrug'ini bajaring.")
        return MAIN_MENU

    username_line = f"🔗 @{user[4]}" if user[4] else ""
    text = (
        "👤 <b>Profil</b>\n\n"
        f"Ism Familiya : {user[2]}\n"
        f"Telefon raqam: {user[3]}\n"
        + (username_line + "\n" if username_line else "")
        + f"Ro'yxat sanasi: {user[5]}"
    )
    await update.message.reply_text(text, parse_mode="HTML")
    return MAIN_MENU


# ─── Foydalanuvchi — Admin bilan bog'lanish ───────────────────────────────────

async def contact_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Kurs haqida ma'lumot olgan bo'lsangiz, "
        "<b>«Kursga qo'shilmoqchiman»</b> deb yozing:",
        parse_mode="HTML",
        reply_markup=buttons.join_course_keyboard(ADMIN_USERNAME),
    )
    return MAIN_MENU


# ─── Admin — Kurs haqida ma'lumot (kiritish) ─────────────────────────────────

async def admin_enter_course_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Kurs haqida ma'lumot yuboring.\n"
        "<i>(Matn, rasm, video, PDF — istalgan formatda)</i>\n\n"
        "Bekor qilish: /cancel",
        parse_mode="HTML",
        reply_markup=buttons.cancel_keyboard(),
    )
    return ADMIN_COURSE_INFO


async def admin_save_course_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ctype, fid, cap = extract_content(update.message)
    db.save_course_info(ctype, fid, cap)
    await update.message.reply_text("✅ Kurs ma'lumoti saqlandi!", reply_markup=buttons.admin_keyboard())
    return MAIN_MENU


# ─── Admin — Kurs narxi (kiritish) ───────────────────────────────────────────

async def admin_enter_course_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Kurs narxi haqida ma'lumot yuboring.\n"
        "<i>(Matn yoki rasm)</i>\n\n"
        "Bekor qilish: /cancel",
        parse_mode="HTML",
        reply_markup=buttons.cancel_keyboard(),
    )
    return ADMIN_COURSE_PRICE


async def admin_save_course_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ctype, fid, cap = extract_content(update.message)
    db.save_course_price(ctype, fid, cap)
    await update.message.reply_text("✅ Kurs narxi saqlandi!", reply_markup=buttons.admin_keyboard())
    return MAIN_MENU


# ─── Admin — Xabar yuborish ───────────────────────────────────────────────────

async def admin_enter_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Barcha foydalanuvchilarga yuboriladigan xabarni kiriting.\n"
        "<i>(Matn, rasm, video, PDF — istalgan formatda)</i>\n\n"
        "Bekor qilish: /cancel",
        parse_mode="HTML",
        reply_markup=buttons.cancel_keyboard(),
    )
    return ADMIN_BROADCAST


async def admin_broadcast_preview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["broadcast_msg"] = update.message
    await update.message.reply_text(
        "⬆️ Yuqoridagi xabar barcha foydalanuvchilarga yuboriladi.\n\nYuborasizmi?",
        reply_markup=buttons.broadcast_confirm_keyboard(),
    )
    return ADMIN_BROADCAST_CONFIRM


async def admin_broadcast_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "broadcast_cancel":
        await query.edit_message_text("❌ Xabar yuborilmadi.")
        await context.bot.send_message(
            query.from_user.id, "Asosiy menyu:", reply_markup=buttons.admin_keyboard()
        )
        return MAIN_MENU

    # Yuborish
    msg = context.user_data.get("broadcast_msg")
    users = db.get_all_active_users()
    sent = failed = 0

    for user in users:
        uid = user[1]
        if uid == ADMIN_ID:
            continue
        try:
            await forward_to(context.bot, msg, uid)
            sent += 1
        except Exception:
            failed += 1

    await query.edit_message_text(
        f"✅ Xabar yuborildi!\n\n"
        f"📨 Yuborildi   : <b>{sent}</b> ta\n"
        f"❌ Yuborilmadi : <b>{failed}</b> ta",
        parse_mode="HTML",
    )
    await context.bot.send_message(
        query.from_user.id, "Asosiy menyu:", reply_markup=buttons.admin_keyboard()
    )
    return MAIN_MENU


# ─── Admin — O'quvchilar ro'yxati ─────────────────────────────────────────────

async def admin_students(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = db.get_all_active_users()
    # Admining o'zini ro'yxatdan chiqarib tashlash
    users = [u for u in users if u[1] != ADMIN_ID]

    if not users:
        await update.message.reply_text("Hozircha ro'yxatda o'quvchi yo'q.")
        return MAIN_MENU

    await update.message.reply_text(f"👨‍🎓 Jami o'quvchilar: <b>{len(users)}</b> ta", parse_mode="HTML")

    for user in users:
        # (id, telegram_id, full_name, phone, username, joined_at, is_active)
        username_line = f"🔗 @{user[4]}" if user[4] else "🔗 Username yo'q"
        text = (
            f"👤 <b>{user[2]}</b>\n"
            f"📞 {user[3]}\n"
            f"{username_line}"
        )
        await update.message.reply_text(
            text,
            parse_mode="HTML",
            reply_markup=buttons.student_card_keyboard(user[1]),
        )
    return MAIN_MENU


async def student_connected_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("O'quvchi ro'yxatdan o'chirildi ✅")

    telegram_id = int(query.data.split("_")[1])
    db.deactivate_user(telegram_id)

    old_text = query.message.text or ""
    await query.edit_message_text(
        old_text + "\n\n✅ Bog'landi — ro'yxatdan o'chirildi",
        parse_mode="HTML",
    )
    return MAIN_MENU


# ─── /cancel ─────────────────────────────────────────────────────────────────

async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    kb = buttons.admin_keyboard() if is_admin(uid) else buttons.user_keyboard()
    await update.message.reply_text("❌ Bekor qilindi.", reply_markup=kb)
    return MAIN_MENU


# ─── Asosiy ──────────────────────────────────────────────────────────────────

def build_app() -> Application:
    app = Application.builder().token(BOT_TOKEN).build()

    # Matn filtrlari
    f_course_info  = filters.Regex(r"^📚 Kurs haqida ma'lumot$")
    f_course_price = filters.Regex(r"^💰 Kurs narxi$")
    f_profile      = filters.Regex(r"^👤 Profil$")
    f_contact      = filters.Regex(r"^📞 Admin bilan bog'lanish$")
    f_broadcast    = filters.Regex(r"^📢 Xabar yuborish$")
    f_students     = filters.Regex(r"^👨‍🎓 O'quvchilar$")

    f_admin  = filters.User(ADMIN_ID)
    f_user   = ~f_admin
    f_any    = filters.ALL & ~filters.COMMAND

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", cmd_start)],
        states={
            REGISTER_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, register_name),
            ],
            REGISTER_PHONE: [
                MessageHandler(filters.CONTACT, register_phone),
                MessageHandler(filters.TEXT & ~filters.COMMAND, register_phone),
            ],
            MAIN_MENU: [
                # ── Foydalanuvchi ──
                MessageHandler(f_course_info  & f_user, user_course_info),
                MessageHandler(f_course_price & f_user, user_course_price),
                MessageHandler(f_contact      & f_user, contact_admin),

                # ── Umumiy (ikkalasiga ham) ──
                MessageHandler(f_profile, show_profile),

                # ── Admin ──
                MessageHandler(f_course_info  & f_admin, admin_enter_course_info),
                MessageHandler(f_course_price & f_admin, admin_enter_course_price),
                MessageHandler(f_broadcast    & f_admin, admin_enter_broadcast),
                MessageHandler(f_students     & f_admin, admin_students),

                # ── Inline tugmalar ──
                CallbackQueryHandler(student_connected_callback, pattern=r"^connected_\d+$"),
            ],
            ADMIN_COURSE_INFO: [
                MessageHandler(f_any, admin_save_course_info),
            ],
            ADMIN_COURSE_PRICE: [
                MessageHandler(f_any, admin_save_course_price),
            ],
            ADMIN_BROADCAST: [
                MessageHandler(f_any, admin_broadcast_preview),
            ],
            ADMIN_BROADCAST_CONFIRM: [
                CallbackQueryHandler(admin_broadcast_confirm, pattern=r"^broadcast_"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cmd_cancel)],
        allow_reentry=True,
    )

    app.add_handler(conv)
    app.add_handler(CommandHandler("myid", cmd_myid))
    return app


if __name__ == "__main__":
    db.init_db()
    application = build_app()
    logging.info("Bot ishga tushdi...")
    application.run_polling(drop_pending_updates=True)
