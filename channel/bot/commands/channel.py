from telegram import Chat, ChatMember, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import CallbackQueryHandler, Filters, MessageHandler

from channel.bot.bot import my_bot
from channel.bot.commands import BaseCommand
from channel.bot.models import ChannelSettings, UserSettings
from channel.bot.utils import build_menu


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

    @BaseCommand.command_wrapper(names=['start', 'reset', 'cancel'])
    def start(self):
        if 'cancel' in self.message.text and self.user_settings.state != UserSettings.IDLE:
            self.message.reply_text('Current action was cancelled')

        self.user_settings.state = UserSettings.IDLE
        buttons = build_menu('Captions', 'Settings')
        self.message.reply_text('What do you want to do?', reply_markup=ReplyKeyboardMarkup(buttons))

    def channel_selector_menu(self, user: UserSettings, prefix: str) -> InlineKeyboardMarkup or None:
        if not user.channels:
            return
        buttons = []
        for channel in user.channels:
            buttons.append(InlineKeyboardButton(channel.name, callback_data=f'{prefix}:{channel.channel_id}'))
        return InlineKeyboardMarkup(build_menu(*buttons))

    def caption_menu(self):
        self.user_settings.state = UserSettings.SET_CAPTION_MENU
        menu = self.channel_selector_menu(self.user_settings, 'change_caption')
        if not menu:
            self.message.reply_text('No channels added yet. To add one forward any message from that channel.')
            return

        self.message.reply_text('For which channel do you want to set a new Caption?',
                                reply_markup=self.channel_selector_menu(self.user_settings, 'change_caption'))

    @BaseCommand.command_wrapper(CallbackQueryHandler, pattern='^change_caption:.*$')
    def pre_set_caption(self):
        channel_id = int(self.update.callback_query.data.split(':')[1])

        member = self.bot.get_chat_member(chat_id=channel_id, user_id=self.user.id)
        if not member.can_change_info:
            self.message.reply_text('You must have change channel info permissions to change the default caption.')
            return

        self.user_settings.current_channel_id = channel_id
        self.user_settings.state = UserSettings.SET_CAPTION

        self.update.callback_query.answer()
        self.message.delete()

        self.message.reply_text(f'Now send me the caption you want to have for your channel. Markdown and HTML are '
                                f'not yet supported.\n\nCurrent Caption:\n{self.user_settings.current_channel.caption}')

    def set_caption(self):
        if not self.message.text:
            self.message.reply_text('You have to send me some text.')
            return
        self.user_settings.current_channel.caption = self.message.text
        self.user_settings.state = UserSettings.IDLE
        self.message.reply_text(f'The caption was set to:\n{self.message.text}')
        self.start()

    @BaseCommand.command_wrapper(MessageHandler, filters=Filters.text)
    def text_message_dispatcher(self):
        try:
            state = self.user_settings.state
            if not state or state == UserSettings.IDLE:
                if self.message.text.lower() == 'captions':
                    self.caption_menu()
            elif state == UserSettings.SET_CAPTION:
                self.set_caption()
        except Exception as error:
            self.message.reply_text('Something went wrong')
            self.start()
            raise error
