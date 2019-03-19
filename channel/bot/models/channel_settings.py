from sqlalchemy import Column, Integer, String

from channel.bot.bot import my_bot


class ChannelSettings(my_bot.Base):
    __tablename__ = 'channel_settings'

    channel_id = Column(Integer, primary_key=True)
    added_by = Column(Integer)
    caption = Column(String(200))
