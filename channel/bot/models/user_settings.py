from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from channel.bot.bot import my_bot
from channel.bot.models.associations import association_user_setting_channel_settings


class UserSettings(my_bot.Base):
    IDLE = 'idle'

    STATES = (IDLE, )

    __tablename__ = 'user_settings'

    user_id = Column(Integer, primary_key=True)
    channels = relationship(
        'ChannelSettings',
        secondary=association_user_setting_channel_settings,
        back_populates='users'
    )

    _state = Column(String(100))

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        if value not in self.STATES:
            raise KeyError('State does no exists')

        self._state = value
        if self not in my_bot.db_session:
            my_bot.db_session.add(self)
        my_bot.db_session.commit()
