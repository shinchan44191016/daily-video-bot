import os
from datetime import datetime
from zoneinfo import ZoneInfo

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Bangladesh time
TZ = ZoneInfo("Asia/Dhaka")

# Store member information in memory
members = {}
daily_submissions = {}


def today():
    return datetime.now(TZ).strftime("%Y-%m-%d")


def member_name(user):
    if user.username:
        return "@" + user.username

    name = user.first_name or ""

    if user.last_name:
        name += " " + user.last_name

    return name.strip() or str(user.id)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ Daily Video Tracker is running!"
    )


async def handle_video(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user
    chat = update.effective_chat

    if not user or not chat:
        return

    user_id = user.id

    # Remember member
    members[user_id] = {
        "name": member_name(user),
        "id": user_id,
    }

    # Today's date
    date = today()

    if date not in daily_submissions:
        daily_submissions[date] = set()

    # Mark submitted
    daily_submissions[date].add(user_id)


async def report(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    # Only allow admins to use report
    member = await context.bot.get_chat_member(
        update.effective_chat.id,
        user.id
    )

    if member.status not in ["administrator", "creator"]:
        return

    date = today()

    submitted = daily_submissions.get(
        date,
        set()
    )

    missing = []

    for user_id, info in members.items():

        if user_id not in submitted:
            missing.append(info["name"])

    text = (
        "📊 DAILY VIDEO REPORT\n\n"
        f"📅 {date}\n\n"
        f"👥 Tracked members: {len(members)}\n"
        f"✅ Submitted: {len(submitted)}\n"
        f"❌ Not submitted: {len(missing)}\n\n"
    )

    if missing:

        text += "❌ DID NOT SUBMIT:\n\n"

        for i, name in enumerate(missing, 1):
            text += f"{i}. {name}\n"

    else:

        text += "🎉 Everyone submitted a video today!"

    await update.message.reply_text(text)


async def status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    member = await context.bot.get_chat_member(
        update.effective_chat.id,
        user.id
    )

    if member.status not in ["administrator", "creator"]:
        return

    date = today()

    submitted = daily_submissions.get(
        date,
        set()
    )

    await update.message.reply_text(
        f"📅 {date}\n\n"
        f"👥 Tracked: {len(members)}\n"
        f"✅ Submitted: {len(submitted)}\n"
        f"❌ Missing: "
        f"{len(members) - len(submitted)}"
    )


def main():

    token = os.environ.get("BOT_TOKEN")

    if not token:
        raise RuntimeError(
            "BOT_TOKEN environment variable is missing."
        )

    application = (
        Application.builder()
        .token(token)
        .build()
    )

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CommandHandler("report", report)
    )

    application.add_handler(
        CommandHandler("status", status)
    )

    application.add_handler(
        MessageHandler(
            filters.VIDEO,
            handle_video
        )
    )

    print("Bot is running...")

    application.run_polling()


if __name__ == "__main__":
    main()
