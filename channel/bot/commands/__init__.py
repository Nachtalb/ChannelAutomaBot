from functools import wraps
from typing import Type, List

from telegram import Bot, Chat, Message, Update, User
from telegram.ext import Handler, run_async as run_async_method

from channel.bot.bot import my_bot
from channel.bot.models import UserSettings
from channel.bot.utils import get_class_that_defined_method


class BaseCommand:
    user: User
    chat: Chat
    message: Message
    update: Update
    bot: Bot
    user_settings: UserSettings or None

    def __init__(self, bot: Bot, update: Update, *args, **kwargs):
        self.user = update.effective_user
        self.chat = update.effective_chat
        self.message = update.effective_message
        self.update = update
        self.bot = my_bot.updater.bot

        self.user_settings = None
        if self.user:
            self.user_settings = my_bot.db_session.query(UserSettings).filter_by(user_id=self.user.id).first()
            if not self.user_settings:
                self.user_settings = BaseCommand.create_user_setting(self.user)

    @staticmethod
    def command_wrapper(handler: Type[Handler] or Handler = None, names: str or List[str] = None,
                        run_async: bool = False, admins_only: bool = None, **kwargs):
        def outer_wrapper(func):
            @wraps(func)
            def wrapper(*inner_args, **inner_kwargs):
                method_class = get_class_that_defined_method(func)

                if (inner_args and isinstance(inner_args[0], method_class)) \
                        or not (len(inner_args) > 1
                                and isinstance(inner_args[0], Bot)
                                and isinstance(inner_args[1], Update)):
                    return func(*inner_args, **inner_kwargs)

                _args, _kwargs = inner_args, inner_kwargs
                if method_class and BaseCommand in method_class.__bases__:
                    instance = method_class(*inner_args, **inner_kwargs)
                    _args = [instance]
                    _kwargs = {}

                if run_async:
                    run_async_method(func(*_args, **_kwargs))
                else:
                    func(*_args, **_kwargs)

            my_bot.add_command(handler=handler, names=names, func=wrapper, admins_only=admins_only, **kwargs)
            return wrapper

        return outer_wrapper

    @staticmethod
    def create_user_setting(user: User) -> UserSettings:
        user = UserSettings(user_id=user.id)

        my_bot.db_session.add(user)
        my_bot.db_session.commit()

        return user


from . import settings
from . import channel_manager
from . import channel_actions
