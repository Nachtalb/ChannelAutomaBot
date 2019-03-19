import logging
from copy import deepcopy

from telegram import ParseMode

from channel.bot import settings as bot_settings
from channel.bot.commands import BaseCommand


class Settings(BaseCommand):
    settings_whitelist = {
        'LOG_LEVEL': 'log_level_changer',
        'ADMINS': None,
    }

    logger = logging.getLogger('Settings')

    @BaseCommand.command_wrapper(names='settings', run_async=True, admins_only=True)
    def runtime_settings_command(self):
        parts = list(filter(None, self.message.text.split(' ')[1:]))
        setting, value, action = None, None, None
        try:
            if len(parts) == 2:
                setting, value = parts
            elif len(parts) == 3:
                setting, value, action = parts
            else:
                raise ValueError

            if not bot_settings or not value or (action and action not in ['+', '-']):
                raise ValueError
        except ValueError:
            self.message.reply_text('Use like this\n/settings <SETTING_NAME> <NEW_VALUE> <- or + if list>')
            return

        if not hasattr(bot_settings, setting) or setting not in self.settings_whitelist:
            self.message.reply_text('Setting not found')
            return

        old_value = getattr(bot_settings, setting, None)

        possible_function = getattr(self, self.settings_whitelist[setting] or '', None)
        old_value_type = type(old_value)
        if old_value_type in (list, set, tuple):
            new_value = list(deepcopy(old_value))
            if action == '+':
                new_value.append(value)
                action_name = 'added'
            elif action == '-' and value in new_value:
                new_value.remove(value)
                action_name = 'removed'
            else:
                self.message.reply_text('Action not defined')
                return

            if isinstance(old_value, tuple):
                new_value = tuple(new_value)
            elif isinstance(old_value, set):
                new_value = set(new_value)

            setattr(bot_settings, setting, new_value)
            if possible_function:
                possible_function(old_value, new_value)

            self.message.reply_text(f'Setting `{setting}` was changed: {action_name} `{value}` in `{old_value}`',
                                    parse_mode=ParseMode.MARKDOWN)
        else:
            if old_value_type in (int, float):
                try:
                    value = old_value_type(value)
                except ValueError:
                    self.message.reply_text(f'Value must be `{old_value_type.__name__}`',
                                            parse_mode=ParseMode.MARKDOWN)
                    return
            setattr(bot_settings, setting, value)

            if possible_function:
                possible_function(old_value, value)

            self.message.reply_text(f'Setting `{setting}` was changed from `{old_value}` to `{value}`',
                                    parse_mode=ParseMode.MARKDOWN)

    def log_level_changer(self, old_value, new_value):
        logging.basicConfig(level=new_value)

        for logger in logging.Logger.manager.loggerDict.values():
            if getattr(logger, 'setLevel', None):
                logger.setLevel(new_value)

