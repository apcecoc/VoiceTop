__version__ = (1, 0, 0)

#       █████  ██████   ██████ ███████  ██████  ██████   ██████ 
#       ██   ██ ██   ██ ██      ██      ██      ██    ██ ██      
#       ███████ ██████  ██      █████   ██      ██    ██ ██      
#       ██   ██ ██      ██      ██      ██      ██    ██ ██      
#       ██   ██ ██       ██████ ███████  ██████  ██████   ██████

#              © Copyright 2025
#           https://t.me/apcecoc
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html
# meta developer: @apcecoc and @Loaaal888

from telethon import events
from telethon.tl.types import Message, Channel, User
from .. import loader, utils
import logging
from typing import Dict, List
from collections import defaultdict

logger = logging.getLogger(__name__)

@loader.tds
class VoiceTopMod(loader.Module):
    """Показывает статистику голосовых сообщений в чате"""
    
    strings = {
    "name": "VoiceTop",
    "en": {
        "processing": "<b>🔄 Counting voice messages...\nAnalyzed: {} messages</b>",
        "no_voices": "<b>❌ No voice messages in this chat</b>",
        "voice_top": "<b>📊 Voice Messages Top\nTotal analyzed: {} messages</b>\n\n{}",
        "voice_stat": "<b>👤 {}</b>: {} voice messages"
    },
    "ru": {
        "processing": "<b>🔄 Идет подсчет голосовых сообщений...\nПроанализировано: {} сообщений</b>",
        "no_voices": "<b>❌ В этом чате нет голосовых сообщений</b>",
        "voice_top": "<b>📊 Топ по голосовым сообщениям\nВсего проанализировано: {} сообщений</b>\n\n{}",
        "voice_stat": "<b>👤 {}</b>: {} голосовых"
    }
}


    def __init__(self):
        self.config = loader.ModuleConfig(
            "MSG_LIMIT", 15000,
            "Максимальное количество сообщений для анализа"
        )

    async def client_ready(self, client, db):
        self.db = db
        self.client = client
        
    async def voicecmd(self, message: Message):
        """Показать статистику голосовых сообщений
        .voice [количество сообщений для анализа]"""
        
        args = utils.get_args_raw(message)
        msg_limit = int(args) if args.isdigit() else self.config["MSG_LIMIT"]
        
        chat = await message.get_chat()
        await message.edit(self.strings["processing"].format(0))
        
        voice_counter: Dict[int, int] = defaultdict(int)
        processed = 0
        update_interval = 1000  # Обновлять статус каждые 1000 сообщений
        
        try:
            async for msg in self.client.iter_messages(chat, limit=msg_limit):
                processed += 1
                if msg.voice:
                    sender = await msg.get_sender()
                    if isinstance(sender, (User, Channel)):
                        voice_counter[sender.id] += 1
                
                if processed % update_interval == 0:
                    await message.edit(
                        self.strings["processing"].format(processed),
                        parse_mode="html"
                    )
                    
        except Exception as e:
            logger.error(f"Error during message processing: {str(e)}")
            await message.edit("❌ Произошла ошибка при подсчете")
            return

        if not voice_counter:
            await message.edit(self.strings["no_voices"])
            return

        sorted_voices = sorted(voice_counter.items(), key=lambda x: x[1], reverse=True)
        
        text = ""
        for i, (user_id, count) in enumerate(sorted_voices, start=1):
            try:
                user = await self.client.get_entity(user_id)
                name = getattr(user, 'first_name', '') or getattr(user, 'title', '') or str(user_id)
                text += self.strings["voice_stat"].format(name, count) + "\n"
            except Exception as e:
                logger.error(f"Error getting user info: {str(e)}")
                continue
                
            if i >= 20:  # Увеличил до 20 пользователей
                break
                
        await message.edit(
            self.strings["voice_top"].format(processed, text),
            parse_mode="html"
        )

    async def voiceconfigcmd(self, message: Message):
        """Изменить настройки модуля
        .voiceconfig [количество сообщений]"""
        args = utils.get_args_raw(message)
        
        if not args or not args.isdigit():
            await message.edit(f"<b>Текущий лимит сообщений для анализа:</b> {self.config['MSG_LIMIT']}")
            return
            
        self.config["MSG_LIMIT"] = int(args)
        await message.edit(f"<b>✅ Установлен новый лимит сообщений:</b> {args}")

    async def vtcmd(self, message: Message):
        """Алиас для команды .voice"""
        await self.voicecmd(message)