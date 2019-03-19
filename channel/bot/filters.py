from telegram import Chat
from telegram.ext import BaseFilter

from channel.bot.utils import is_media_message


class Filters:
    class _Media(BaseFilter):
        name = 'Filters.media'

        def filter(self, message):
            return is_media_message(message)

    media = _Media()
    """:obj:`Filter`: Messages sent is a media file."""

    class _Channel(BaseFilter):
        name = 'Filters.channel'

        def filter(self, message):
            return message.chat.type in [Chat.CHANNEL]

    channel = _Channel()
    """:obj:`Filter`: Messages sent in a channels."""
