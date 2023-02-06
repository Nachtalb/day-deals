# Day Deal Telegram Bot

This is the bot used for the "[Angebote des Tages (Schweiz)][channel]" channel.
Said channel posts daily and weekly spacial offers of various swiss online
retailers such as [digitec][digitec].

[![Angebote des Tages (Schweiz)](https://img.shields.io/badge/-Telegram-0088CC?logo=telegram&logoColor=white)][channel]

## Supported Sites

There are not many retailers with specifically day / week deals that I know
of so the list is a bit small. But these are basically all the ones the swiss
population as a whole really cares about.

| Retailer | Type | Time | Method |
| --- | --- | --- | --- |
| [digitec][digitec] | Daily | 00:00 | Via a [graphql endpoint][digitec-code] |
| [Galaxus][galaxus] | Daily | 00:00 | Via a [graphql endpoint][digitec-code] |
| [20min][20min] | Daily | 00:00 | Scraping the [website][20min-code] |
| [20min][20min-weekly] | Weekly | Mo 00:00 | Scraping the [website][20min-code] |
| [Brack / daydeal.ch][daydeal] | Daily | 09:00 | Scraping the [website][daydeal-code] |
| [Brack / daydeal.ch][daydeal-week] | Weekly | Mo 09:00 | Scraping the [website][daydeal-code] |

## Setup

```bash
# Clone repo
git clone https://github.com/Nachtalb/day-deals
cd day-deals

# Install dependencies
pip install -r requirements.txt

# Copy sample config and adjust values inside
cp config.sample.json config.json
```

You can get a bot `token` from [BotFather][botfather]. The `chat_id` of the
chat the deals are posted to can be retrieved by using an unofficial telegram
client such as [64gram][64gram] (desktop), [Plus][plus] or via another bot like
[IDBot][idbot].

## Usage

Just run the bot:

```bash
python day.py
```

To run it periodically you can easily create a cronjob:

```bash
5 * * * * /path/to/python /path/to/day-deals/day.py 2>&1 | /usr/bin/logger -t day-deals
```

The `2>1 | /urs/bin/logger -t day-deals` is optional. It just makes sure that
all outputs are correctly logged to the crontab logs.

[channel]: https://t.me/angebote_des_tages_schweiz
[digitec]: https://www.digitec.ch/
[digitec-code]: https://github.com/Nachtalb/day-deals/blob/fc20d5b33ceba6a1a289479c7c76c19a66af82b6/day.py#L12-L80
[galaxus]: https://www.galaxus.ch/
[20min]: https://myshop.20min.ch/de_DE/category/angebot-des-tages
[20min-weekly]: https://myshop.20min.ch/de_DE/category/wochenangebot
[20min-code]: https://github.com/Nachtalb/day-deals/blob/fc20d5b33ceba6a1a289479c7c76c19a66af82b6/day.py#L129-L169
[daydeal]: https://daydeal.ch
[daydeal-week]: https://www.daydeal.ch/deal-of-the-week
[daydeal-code]: https://github.com/Nachtalb/day-deals/blob/fc20d5b33ceba6a1a289479c7c76c19a66af82b6/day.py#L83-L126
[botfather]: https://t.me/BotFather
[64gram]: https://github.com/TDesktop-x64/tdesktop
[plus]: https://play.google.com/store/apps/details?id=org.telegram.plus&hl=en&gl=US
[idbot]: https://t.me/myidbot
