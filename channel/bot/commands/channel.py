from telegram import Chat, ChatMember
from telegram.ext import Filters, MessageHandler

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

            message = 'Channel was updated'
            if not channel:
                channel = ChannelSettings(channel_id=possible_channel.id,
                                          added_by=self.user.id,
                                          users=[self.user_settings])
                my_bot.db_session.add(channel)
                message = 'Channel was added'
            elif self.user_settings not in channel.users:
                channel.users.append(self.user_settings)
                message = 'Channel was added'

            channel.update_from_chat(possible_channel)
            my_bot.db_session.commit()
            self.message.reply_text(message)
