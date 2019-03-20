from typing import List

from telegram import Chat, ChatMember, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ParseMode
from telegram.error import Unauthorized
from telegram.ext import CallbackQueryHandler, Filters, MessageHandler

from channel.bot.bot import my_bot
from channel.bot.commands import BaseCommand
from channel.bot.models import ChannelSettings, UserSettings
from channel.bot.utils import build_menu
from channel.bot.filters import Filters as OwnFilters


class ChannelManager(BaseCommand):
    @BaseCommand.command_wrapper(MessageHandler, run_async=True, filters=Filters.forwarded & (~ OwnFilters.channel))
    def add_channel(self):
        possible_channel = self.message.forward_from_chat

        if not possible_channel or possible_channel.type != Chat.CHANNEL or self.chat.type != Chat.PRIVATE:
            return

        member: ChatMember or None
        try:
            member = possible_channel.get_member(my_bot.me().id)
        except Unauthorized:
            member = None

        if not member or member.status == member.LEFT:
            self.message.reply_text('I have to be a member of this chat to function')
            return

        user_member: ChatMember
        user_member = possible_channel.get_member(self.user.id)

        if user_member.status not in [user_member.ADMINISTRATOR, user_member.CREATOR]:
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

        self.user_settings.current_channel = None
        self.user_settings.state = UserSettings.IDLE
        buttons = build_menu('Captions', 'Settings', footer_buttons=['Cancel current action'])
        self.message.reply_text('What do you want to do?', reply_markup=ReplyKeyboardMarkup(buttons))

    def channel_selector_menu(self, user: UserSettings, prefix: str,
                              header_buttons: List[InlineKeyboardButton] = None,
                              footer_buttons: List[InlineKeyboardButton] = None) -> InlineKeyboardMarkup or None:
        if not user.channels:
            return
        buttons = []
        for channel in user.channels:
            buttons.append(InlineKeyboardButton(channel.name, callback_data=f'{prefix}:{channel.channel_id}'))
        return InlineKeyboardMarkup(build_menu(*buttons, header_buttons=header_buttons, footer_buttons=footer_buttons))

    def caption_menu(self):
        menu = self.channel_selector_menu(self.user_settings, 'change_caption')
        if not menu:
            self.message.reply_text('No channels added yet. To add one forward any message from that channel.')
            return

        self.user_settings.state = UserSettings.SET_CAPTION_MENU
        self.message.reply_text('For which channel do you want to set a new Caption?', reply_markup=menu)

    def settings_menu(self):
        footer_buttons = [InlineKeyboardButton('Update Channels', callback_data='update_channels'),
                          InlineKeyboardButton('Back', callback_data='cancel')]
        menu = self.channel_selector_menu(self.user_settings, 'change_settings_menu', footer_buttons=footer_buttons)

        if not menu:
            self.message.reply_text('No channels added yet. To add one forward any message from that channel.')
            return

        self.user_settings.state = UserSettings.SETTINGS_MENU
        self.message.reply_text('What do you want to do?', reply_markup=menu)

    @BaseCommand.command_wrapper(CallbackQueryHandler, pattern='^update_channels$')
    def update_channels(self):
        for channel in self.user_settings.channels:
            channel.update()
        my_bot.db_session.commit()
        self.message.reply_text('Channels updated')
        self.message.delete()
        self.start()

    @BaseCommand.command_wrapper(CallbackQueryHandler, pattern='^change_settings_menu:.*$')
    def channel_settings_menu(self):
        channel_id = int(self.update.callback_query.data.split(':')[1])
        self.message.delete()

        self.user_settings.current_channel_id = channel_id
        self.user_settings.state = UserSettings.CHANNEL_SETTINGS_MENU

        buttons = ReplyKeyboardMarkup(build_menu('Remove', 'Cancel'))

        self.message.reply_text(f'Settings for {self.user_settings.current_channel.name}', reply_markup=buttons)

    def remove_channel_confirm_dialog(self):
        self.user_settings.state = UserSettings.PRE_REMVOE_CHANNEL
        self.message.reply_text(f'Are you sure you want to remove: {self.user_settings.current_channel.name}?',
                                reply_markup=ReplyKeyboardMarkup(build_menu('Yes', 'No')))

    def remove_channel_confirmation(self):
        if self.message.text.lower() == 'yes':
            self.user_settings.channels.remove(self.user_settings.current_channel)
            self.message.reply_text('Channel was removed')
        elif self.message.text.lower() != 'no':
            self.message.reply_text('Either hit yes or no')
            return
        self.start()

    @BaseCommand.command_wrapper(CallbackQueryHandler, pattern='^change_caption:.*$')
    def pre_set_caption(self):
        channel_id = int(self.update.callback_query.data.split(':')[1])

        member = self.bot.get_chat_member(chat_id=channel_id, user_id=self.user.id)
        if not member.can_change_info and not member.status == member.CREATOR:
            self.message.reply_text('You must have change channel info permissions to change the default caption.')
            return

        self.user_settings.current_channel_id = channel_id
        self.user_settings.state = UserSettings.SET_CAPTION

        self.update.callback_query.answer()
        self.message.delete()

        self.message.reply_text(f'Now send me the caption you want to have for your channel - '
                                f'{self.user_settings.current_channel.name}. \n\nCurrent Caption:\n'
                                f'{self.user_settings.current_channel.caption}',
                                reply_markup=ReplyKeyboardMarkup(build_menu('Clear', 'Cancel')),
                                parse_mode=ParseMode.MARKDOWN)

    def clear_caption(self):
        self.user_settings.current_channel.caption = None
        self.message.reply_text(f'Caption for {self.user_settings.current_channel.name} cleared')
        self.start()

    @BaseCommand.command_wrapper(CallbackQueryHandler, pattern='^(home|cancel)$')
    def get_home(self):
        self.message.delete()
        self.start()

    def set_caption(self):
        if not self.message.text:
            self.message.reply_text('You have to send me some text.')
            return
        self.user_settings.current_channel.caption = self.message.text_markdown
        self.user_settings.state = UserSettings.IDLE
        self.message.reply_text(f'The caption of {self.user_settings.current_channel.name} was set to:'
                                f'\n{self.message.text_markdown}', parse_mode=ParseMode.MARKDOWN)
        self.start()

    @BaseCommand.command_wrapper(MessageHandler, filters=Filters.text & (~ OwnFilters.channel))
    def text_message_dispatcher(self):
        try:
            state = self.user_settings.state
            text = self.message.text.lower()
            if text in ['cancel', 'home', 'cancel current action']:
                self.start()
            elif not state or state == UserSettings.IDLE:
                if text == 'captions':
                    self.caption_menu()
                if text == 'settings':
                    self.settings_menu()
            elif state == UserSettings.SET_CAPTION:
                if text == 'clear':
                    self.clear_caption()
                else:
                    self.set_caption()
            elif state == UserSettings.CHANNEL_SETTINGS_MENU:
                if text == 'remove':
                    self.remove_channel_confirm_dialog()
            elif state == UserSettings.PRE_REMVOE_CHANNEL:
                self.remove_channel_confirmation()
        except Exception as error:
            self.message.reply_text('Something went wrong')
            self.start()
            raise error
