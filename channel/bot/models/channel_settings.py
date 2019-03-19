from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from telegram import Chat

from channel.bot.bot import my_bot
from channel.bot.models.associations import association_user_setting_channel_settings


class ChannelSettings(my_bot.Base):
    __tablename__ = 'channel_settings'

    channel_id = Column(Integer, primary_key=True)
    channel_username = Column(String(200))
    channel_title = Column(String(200))

    added_by = Column(Integer)
    caption = Column(String(200))

    users = relationship(
        'UserSettings',
        secondary=association_user_setting_channel_settings,
        back_populates='channels'
    )

    def update_from_chat(self, chat: Chat):
        self.channel_username = chat.username
        self.channel_title = chat.title

    @property
    def name(self) -> str:
        return self.channel_title or '@' + self.channel_username

    @property
    def chat(self) -> Chat:
        return my_bot.updater.bot.get_chat(self.channel_id)

    def update(self):
        self.update_from_chat(self.chat)
