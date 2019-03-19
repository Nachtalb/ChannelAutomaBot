from telegram import Chat
from telegram.ext import BaseFilter


class Filters:

    class _Channel(BaseFilter):
        name = 'Filters.channel'

        def filter(self, message):
            return message.chat.type in [Chat.CHANNEL]

    channel = _Channel()
    """:obj:`Filter`: Messages sent in a channels."""
