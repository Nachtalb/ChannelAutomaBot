from telegram import Bot, ParseMode, Update
from telegram.ext import Filters, MessageHandler

from channel.bot.bot import my_bot
from channel.bot.commands import BaseCommand
from channel.bot.filters import Filters as OwnFilters
from channel.bot.models import ChannelSettings
from channel.bot.utils import is_media_message


class ChannelActions(BaseCommand):
    channel_settings: ChannelSettings

    def __init__(self, bot: Bot, update: Update, *args, **kwargs):
        super().__init__(bot, update, *args, **kwargs)
        self.channel_settings = my_bot.db_session.query(ChannelSettings).filter_by(channel_id=self.chat.id).first()

    @BaseCommand.command_wrapper(MessageHandler, filters=OwnFilters.channel & (Filters.text | OwnFilters.media))
    def auto_caption(self):
        if not self.channel_settings or not self.channel_settings.caption:
            return

        caption = self.channel_settings.caption
        if self.message.text and not self.message.text.endswith(caption):
            self.message.edit_text(f'{self.message.text_markdown}\n\n{caption}', parse_mode=ParseMode.MARKDOWN)
        if is_media_message(self.message) and (self.message.caption is None
                                               or not self.message.caption.endswith(caption)):
            self.message.edit_caption(caption=f'{self.message.caption_markdown or ""}\n\n{caption}',
                                      parse_mode=ParseMode.MARKDOWN)
