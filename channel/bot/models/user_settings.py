from sqlalchemy import Column, Integer

from channel.bot.bot import my_bot


class UserSettings(my_bot.Base):
    __tablename__ = 'user_settings'

    user_id = Column(Integer, primary_key=True)
