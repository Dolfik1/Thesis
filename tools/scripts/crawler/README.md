# Telegram Crawler

#### This script used to catch data from telegram chats.

## Instructions

### Preparation

The very first step requires you to obtain a valid Telegram API key (API id/hash pair). If you already have one you can skip this step, otherwise:

1. Visit https://my.telegram.org/apps and log in with your Telegram Account.
2. Fill out the form to register a new Telegram application.
3. Done. The API key consists of two parts: App api_id and App api_hash.

The API key obtained in the previous step defines a token for your application allowing you to access the Telegram database using the MTProto API — it is therefore required for all authorizations of both Users and Bots.

Create a new config.ini file at the root of your working directory, copy-paste the following and replace the api_id and api_hash values with your own. This is the preferred method because allows you to keep your credentials out of your code without having to deal with how to load them:

```ini
[pyrogram]
api_id = 12345
api_hash = 0123456789abcdef0123456789abcdef
```

### Start crawler without Docker

```bash
pip install -r requirements.txt
python telegram_crawler.py --chats me
```

If you run script first time, you should specify your phone number and activation code.

You can specify chats for parsing via `--chats` argument.

### Start crawler in Docker

Before you run crawler in Docker, you should run crawler without docker and enter authorization data (phone number and activation code).

```bash
docker build -t telegram_crawler .
docker run -d -it --name=tg_crawler telegram_crawler --chats me
```

You can execute `copy_data.sh` script, to copy parsed data from container to `results` folder.


### Chats used for parsing
 
 
--chats volgograd baaardak habragram BashkortostanR chatbel bludcaliforni geekbeardtvchat jetcity dobro_chat PeaceDoBall Kavardak20i

@chat_pikabu

@pikabu_chat

@chat_msk

@kinolepra

@soaplepra

@IslandOfHope

@region73_ulyanovsk

@pepper_peppercorns

@Geopolitica

@pandaChat

@msk24

@Poehavshie

@khabchat

@printer_ru

@kazanchat

@samchat

@znakomstva_rus

@omsk_chat

@kinochatic

@Penzachat

@dosug38chat

@NeLiOne

@soc42

@yorsh1

@samara_chat

@chatminsk

@nashChat

@ask911

@readallhumans

@straightup_chat

@kinolepra

https://telegram-club.ru/open?page=3&per-page=50


@startupchat

@ekbstile

@chelchat

@psikhpodderzhka

@TogliattiChat

@barnaulers

@tiptp

@ufarb02

@vlchat

@voiceofdon

@freedomzone

@perm59naididruzei

@andromedica

@khabara_ru

@crimeaa

@smolchat

@ekaterinburgg

@mosclub

@pldnprivate

@ufachat

@somniya

@tvchat

@vegan_chat

@saratov_public

@ekbchat

@mi_mino

@chat25

@chatobovsem

@kinochat

@lawyerchat

@bigdata_ru

@sadnesschat

@chat_irk

@lipetskcity

@stavrchat

@yelik

@ooooooooooooooo

@myyyaaa

@kurgan_chat

@typsy

@chatUSSR

@esoterics_chat

@JoyReactr

@kamyshin_friends

@gomelbel

@techat

@TomskChat

@comixlepra

@wintersports

@dmd_chat

@ru_philosophy

@grodnochat

@physpub

@krasnodarchatik

@newtema

@konfat

@chitalnya

@knigoklub

@samarachat

@our_refuge

@coinmarket1

@ru_travel

@chelyabinskk

@ittalks

@to_best_world

@TalkChat

@ru_politics

@konfa

@blagoveshensk_chat

@murom33

@lampach

@nedimon_saratov

@truefilms

@litegroup

@soc93

@dogschat - HERE

@tomskpublic

@reptiloids_chat

@freedomlife1

@sfo_chat

@trinityme

@mensworldclub

@leftypol

@5a1544e06d02a

@lingvachat

@mynutka

@chat_dv

@chat_obo_vsem_i_ni_o_chem

@kowatnik

@osmiumlc

@5a24800809c7c

@IvChat

@ru2chfiz

@chattltnew

@LCFUB

@psychologme

@club_chat

@vomrake

@vlg2ch

@bloop_xoxo

@bsdk

@chat_continent

@ptalk

@techno_chat

@rider_pro

@pirozhok

@PsyPortal

@jiveinc



https://telegram-club.ru/open?page=11&per-page=50