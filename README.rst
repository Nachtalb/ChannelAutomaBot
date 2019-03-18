ChannelAutomaBot
================

`@ChannelAutomaBot <https://t.me/ChannelAutomaBot>`__ \|
`GitHub <https://github.com/Nachtalb/ChannelAutomaBot>`__

.. contents:: Table of Contents


What I do
---------

Some automation stuff for channels. Eg. automatically converting video to mp3 or adding captions to sent messages.


Development
-----------

For the project I chose `buildout <http://www.buildout.org/en/latest/contents.html>`__ instead of the default pip way.
I manly did this because it makes installation easier. I recommend to be in an virtualenv for any project, but this is
up to you. Now for the installation:

.. code:: bash

   ln -s development.cfg buildout.cfg
   python bootstrap.py
   bin/buildout

And everything should be installed. Now you can copy and configure your settings.

.. code:: bash

   cp channel/bot/settings.example.py  channel/bot/settings.py


Get a Telegram Bot API Token > `@BotFather <https://t.me/BotFather>`__ and put it inside your ``settings.py``.

To run the bot simply run

.. code:: bash

   bin/bot


Copyright
---------

Thank you for using `@ChannelAutomaBot <https://t.me/ChannelAutomaBot>`__.

Made by `Nachtalb <https://github.com/Nachtalb>`_ | This extension licensed under the `GNU General Public License v3.0 <https://github.com/Nachtalb/DanbooruChannelBot/blob/master/LICENSE>`_.
