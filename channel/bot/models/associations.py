from sqlalchemy import Column, ForeignKey, Integer, Table

from channel.bot.bot import my_bot

association_user_setting_channel_settings = Table(
    'user_setting_channel_settings', my_bot.Base.metadata,

    Column('user_id', Integer, ForeignKey('user_settings.user_id')),
    Column('channel_id', Integer, ForeignKey('channel_settings.channel_id'))
)
