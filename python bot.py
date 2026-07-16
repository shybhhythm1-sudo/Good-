#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
بوت تحميل الفيديوهات من جميع منصات التواصل الاجتماعي
Universal Video Downloader Bot
يدعم: تيك توك، إنستغرام، فيسبوك، تويتر، يوتيوب، وأكثر من 1000 موقع
"""

import subprocess
import sys
import os

def install_requirements():
    """تثبيت المكتبات المطلوبة تلقائياً"""
    required = ['python-telegram-bot', 'yt-dlp', 'requests']
    for package in required:
        try:
            __import__(package.replace('-', '_').replace('python-telegram-bot', 'telegram'))
        except ImportError:
            print(f"جاري تثبيت {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

install_requirements()

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp
import tempfile
import re
import logging

# تفعيل التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# توكن البوت - غيّره فوراً!
BOT_TOKEN = "8799967091:AAG64VvKujkQ0ItQlzIurW31ZQCDPV6ZIIc"

def download_video(url):
    """تحميل الفيديو من أي منصة"""
    try:
        ydl_opts = {
            'format': 'best[height<=720]',  # جودة متوسطة لتجنب حجم كبير
            'outtmpl': '%(id)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'noplaylist': True,  # تحميل فيديو واحد فقط
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            ydl_opts['outtmpl'] = os.path.join(tmpdir, '%(id)s.%(ext)s')
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                video_path = ydl.prepare_filename(info)
                
                # التحقق من وجود الملف
                if os.path.exists(video_path):
                    return video_path, info.get('title', 'فيديو'), info.get('duration', 0)
                else:
                    return None, "لم يتم العثور على الملف", 0
                
    except Exception as e:
        logger.error(f"خطأ في التحميل: {e}")
        return None, str(e), 0

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة أمر /start"""
    welcome_text = """
🎬 *مرحباً بك في بوت تحميل الفيديوهات!* 🎬

📱 *يدعم أكثر من 1000 موقع:*
• تيك توك (TikTok)
• إنستغرام (Instagram)
• فيسبوك (Facebook)
• تويتر/X (Twitter)
• يوتيوب (YouTube)
• سناب شات (Snapchat)
• وغيرها الكثير!

✨ *كيفية الاستخدام:*
1. انسخ رابط الفيديو من أي منصة
2. الصق الرابط هنا
3. انتظر حتى يتم تحميل الفيديو وإرساله لك

💡 أرسل رابط الفيديو للبدء!
    """
    
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة أمر /help"""
    help_text = """
🆘 *المساعدة*

*الأوامر المتاحة:*
/start - بدء البوت
/help - عرض رسالة المساعدة

*المنصات المدعومة:*
• تيك توك، إنستغرام، فيسبوك
• تويتر/X، يوتيوب، سناب شات
• ريدت، بنترست، فيميو
• وأكثر من 1000 موقع آخر!

*كيفية التحميل:*
1. افتح التطبيق الذي يحتوي على الفيديو
2. اختر الفيديو واضغط "مشاركة" أو "نسخ الرابط"
3. الصق الرابط هنا في المحادثة

⚠️ *ملاحظات:*
• تأكد من أن الرابط عام (ليس خاص)
• بعض الفيديوهات الطويلة جداً قد لا تعمل
• الجودة القصوى 720p لتجنب مشاكل الحجم
    """
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الرسائل النصية"""
    text = update.message.text
    
    if not text:
        return
    
    # التحقق من وجود رابط
    url_pattern = r'https?://\S+'
    urls = re.findall(url_pattern, text)
    
    if not urls:
        await update.message.reply_text(
            "❌ لم أجد رابطاً في رسالتك.\n\n"
            "الرجاء إرسال رابط فيديو صحيح من أي منصة."
        )
        return
    
    url = urls[0]
    
    # إرسال رسالة انتظار
    status_message = await update.message.reply_text(
        "⏳ جاري تحميل الفيديو...\n"
        "الرجاء الانتظار قليلاً"
    )
    
    # تحميل الفيديو
    video_path, title, duration = download_video(url)
    
    if video_path and os.path.exists(video_path):
        try:
            # التحقق من حجم الملف (تيليجرام يسمح حتى 50MB للبوتات)
            file_size = os.path.getsize(video_path)
            max_size = 50 * 1024 * 1024  # 50MB
            
            if file_size > max_size:
                await status_message.edit_text(
                    "❌ حجم الفيديو كبير جداً (أكثر من 50MB).\n"
                    "تيليجرام لا يسمح بإرسال ملفات بهذا الحجم."
                )
                os.remove(video_path)
                return
            
            # إرسال الفيديو
            await update.message.reply_video(
                video=open(video_path, 'rb'),
                caption=f"🎬 {title[:200]}",
                supports_streaming=True
            )
            
            # حذف رسالة الحالة
            await status_message.delete()
            
            # حذف الملف المؤقت
            os.remove(video_path)
            
        except Exception as e:
            logger.error(f"خطأ في إرسال الفيديو: {e}")
            await status_message.edit_text(
                "❌ حدث خطأ أثناء إرسال الفيديو.\n"
                "الرجاء المحاولة مرة أخرى."
            )
    else:
        await status_message.edit_text(
            f"❌ فشل تحميل الفيديو.\n\n"
            f"الأسباب المحتملة:\n"
            f"• الرابط غير صحيح أو خاص\n"
            f"• الفيديو غير متاح\n"
            f"• المنصة غير مدعومة\n\n"
            f"تأكد من أن الرابط عام وحاول مرة أخرى."
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الأخطاء"""
    logger.warning(f'تحديث {update} سبب خطأ {context.error}')
    
    if update and update.message:
        await update.message.reply_text(
            "❌ عذراً، حدث خطأ غير متوقع.\n"
            "الرجاء المحاولة مرة أخرى لاحقاً."
        )

def main():
    """تشغيل البوت"""
    # إنشاء التطبيق
    application = Application.builder().token(BOT_TOKEN).build()
    
    # إضافة المعالجات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)
    
    # تشغيل البوت
    print("🤖 البوت يعمل الآن...")
    print("يدعم تحميل الفيديوهات من أكثر من 1000 موقع!")
    print("اضغط Ctrl+C لإيقاف البوت")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()