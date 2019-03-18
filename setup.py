from setuptools import find_packages, setup

version = '0.0.1.dev0'

setup(name='ChannelAutomaBot',
      version=version,
      description='Some automation stuff for channels. Eg. automatically converting video to mp3 or adding captions '
                  'to sent messages.',
      long_description=f'{open("README.rst").read()}\n{open("CHANGELOG.rst").read()}',

      author='Nachtalb',
      url='https://github.com/Nachtalb/ChannelAutomaBot',
      license='GPL3',

      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['channel'],
      include_package_data=True,
      zip_safe=False,

      install_requires=[
          'mr.developer',
          'python-telegram-bot',
          'requests_html',
          'emoji',
          'wrapt',
          'SQLAlchemy',
      ],

      entry_points={
          'console_scripts': [
              'bot = channel.bot.bot:main',
          ]
      })
