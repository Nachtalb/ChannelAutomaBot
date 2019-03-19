from telegram import Chat, ChatMember, ReplyKeyboardMarkup
from telegram.ext import MessageHandler

from channel.bot.bot import my_bot
from channel.bot.commands import BaseCommand
from channel.bot.models import ChannelSettings


class Channel(BaseCommand):
    @BaseCommand.command_wrapper(MessageHandler, run_async=True, filters=Filters.forwarded)
    def add_channel(self):
        possible_channel = self.message.forward_from_chat

        if not possible_channel or possible_channel.type != Chat.CHANNEL or self.chat.type != Chat.PRIVATE:
            return

        member: ChatMember
        member = possible_channel.get_member(my_bot.me().id)

        if member.status == member.LEFT:
            self.message.reply_text('I have to be a member of this chat to function')

        user_member: ChatMember
        user_member = possible_channel.get_member(self.user.id)

        if user_member.status != user_member.ADMINISTRATOR:
            self.message.reply_text('You must be an admin yourself to use me.')
        else:
            channel = my_bot.db_session.query(ChannelSettings).filter_by(channel_id=possible_channel.id).first()
            if not channel:
                channel = ChannelSettings(channel_id=possible_channel.id, added_by=self.user.id)
                my_bot.db_session.add(channel)
                my_bot.db_session.commit()
                self.message.reply_text('Channel was added')
            else:
                self.message.reply_text('Channel already added')

    @BaseCommand.command_wrapper(names=['start', 'reset'])
    def start(self):
        buttons = [
            ['Caption', ],
            ['Settings', ]
        ]
        self.message.reply_text('What do you want to do?', reply_markup=ReplyKeyboardMarkup(buttons))
