import logging
import os
import sys
from threading import Thread
from typing import Callable, List, Type

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from telegram import Bot, Update, User
from telegram.ext import CommandHandler, Filters, Handler, Updater, messagequeue, MessageHandler, CallbackQueryHandler
from telegram.utils.request import Request

from channel.bot import settings
from .settings import ADMINS, LOG_LEVEL, MODE, TELEGRAM_API_TOKEN

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=LOG_LEVEL)


class MQBot(Bot):
    """subclass of Bot which delegates send method handling to MQ"""

    def __init__(self, *args, is_queued_def=True, mqueue=None, **kwargs):
        super(MQBot, self).__init__(*args, **kwargs)
        # below 2 attributes should be provided for decorator usage
        self._is_messages_queued_default = is_queued_def
        self._msg_queue = mqueue or messagequeue.MessageQueue()

    def __del__(self):
        try:
            self._msg_queue.stop()
        except:
            pass
        super(MQBot, self).__del__()

    @messagequeue.queuedmessage
    def send_message(self, *args, **kwargs):
        """Wrapped method would accept new `queued` and `isgroup`
        OPTIONAL arguments"""
        return super(MQBot, self).send_message(*args, **kwargs)


class MyBot:
    def __init__(self, token: str, mode: str, mode_config: dict = None, admins: List[str] = None):
        self.token = token
        self.mode = mode
        self.mode_config = mode_config or {}
        self.admins = admins or []

        self.updater = None
        self.logger = logging.getLogger(self.__class__.__name__)

        self.db_engine = create_engine(settings.DATABASE)

        Session = sessionmaker(bind=self.db_engine)
        self.db_session = Session()

        self.Base = declarative_base()

    def start(self):
        queue = messagequeue.MessageQueue(all_burst_limit=29, all_time_limit_ms=1017)
        request = Request(con_pool_size=8)
        bot = MQBot(self.token, request=request, mqueue=queue)

        self.updater = Updater(bot=bot)

        self.add_command(func=self.restart, admins_only=True)

        self.log_self()
        self.send_message_if_reboot()

        # noinspection PyUnresolvedReferences
        from . import models

        self.Base.metadata.create_all(self.db_engine)

        # noinspection PyUnresolvedReferences
        from . import commands

        if self.mode == 'webhook':
            self.updater.start_webhook(listen=self.mode_config['listen'], port=self.mode_config['port'],
                                       url_path=self.mode_config['url_path'])
            self.updater.bot.set_webhook(url=self.mode_config['url'])
        else:
            self.updater.start_polling()
            self.updater.idle()

    def log_self(self):
        me = self.me()
        self.logger.info(f'Start {self.mode} as: @{me.username} [{me.link}]')

    def me(self) -> User:
        return self.updater.bot.get_me()

    def add_command(self, handler: Type[Handler] or Handler = None, names: str or List[str] = None,
                    func: Callable = None, admins_only: bool = False, **kwargs):
        handler = handler or CommandHandler
        if admins_only:
            admin_filter = Filters.user(username=self.admins)
            if 'filters' in kwargs:
                kwargs['filters'] = kwargs['filters'] & admin_filter
            else:
                kwargs['filters'] = admin_filter

        if isinstance(handler, Handler):
            self.updater.dispatcher.add_handler(handler=handler)
        elif handler == MessageHandler:
            self.updater.dispatcher.add_handler(handler=handler(kwargs.get('filters', Filters.all), func))
        elif handler == CallbackQueryHandler:
            self.updater.dispatcher.add_handler(handler=handler(func, **kwargs))
        else:
            if not names:
                names = [func.__name__]
            elif not isinstance(names, List):
                names = [names]

            for name in names:

                self.updater.dispatcher.add_handler(handler=handler(name, func, **kwargs))

    def stop_and_restart(self, chat_id):
        """Gracefully stop the Updater and replace the current process with a new one.
        """
        self.logger.info('Restarting: stopping')
        self.updater.stop()
        self.logger.info('Restarting: starting')
        os.execl(sys.executable, sys.executable, *sys.argv + [f'is_restart={chat_id}'])

    def restart(self, bot: Bot, update: Update):
        """Start the restarting process

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
        """
        update.message.reply_text('Bot is restarting...')
        Thread(target=lambda: self.stop_and_restart(update.message.chat_id)).start()

    def send_message_if_reboot(self):
        args = sys.argv
        is_restart_arg = [item for item in args if item.startswith('is_restart')]

        if any(is_restart_arg):
            chat_id = is_restart_arg[0].split('=')[1]
            self.updater.bot.send_message(chat_id, 'Bot has successfully restarted.')


my_bot: MyBot


def main():
    global my_bot
    my_bot = MyBot(TELEGRAM_API_TOKEN, mode=MODE['active'], mode_config=MODE.get('configuration'), admins=ADMINS)
    my_bot.start()


if __name__ == '__main__':
    main()
