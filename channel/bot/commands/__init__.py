from functools import wraps
from typing import Type

from telegram import Bot, Chat, Message, Update, User
from telegram.ext import Handler, run_async as run_async_method

from channel.bot.bot import my_bot
from channel.bot.models import UserSettings
from channel.bot.utils import get_class_that_defined_method


class BaseCommand:
    user: User
    chat: Chat
    message: Message
    user_settings: UserSettings

    def __init__(self, bot: Bot, update: Update, *args, **kwargs):
        self.user = update.effective_user
        self.chat = update.effective_chat
        self.message = update.effective_message

        self.user_settings = my_bot.db_session.query(UserSettings).filter_by(user_id=self.user.id).first()
        if not self.user_settings:
            self.user_settings = BaseCommand.create_user_setting(self.user)

    @staticmethod
    def command_wrapper(handler: Type[Handler] or Handler = None, name: str = None, run_async: bool = False, **kwargs):
        def outer_wrapper(func):
            @wraps(func)
            def wrapper(bot: Bot, update: Update, *inner_args, **inner_kwargs):
                method_class = get_class_that_defined_method(func)

                _args, _kwargs = [], {}
                if method_class and BaseCommand in method_class.__bases__:
                    instance = method_class(bot, update, *inner_args, **inner_kwargs)
                    _args = [instance]
                else:
                    _args.extend([bot, update])
                    _args.extend(inner_args)
                    _kwargs = inner_kwargs

                if run_async:
                    run_async_method(func(*_args, **_kwargs))
                else:
                    func(*_args, **_kwargs)

            my_bot.add_command(handler=handler, name=name, func=wrapper, **kwargs)
            return wrapper

        return outer_wrapper


    @staticmethod
    def create_user_setting(user: User) -> UserSettings:
        user = UserSettings(user_id=user.id)

        my_bot.db_session.add(user)
        my_bot.db_session.commit()

        return user


from . import settings
