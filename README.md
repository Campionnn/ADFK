# ADFK

### IMPORTANT: This was last updated right before they added the unit manager QoL feature, it still mostly works but it can break in certain circumstances. The new golden portals have not been added either. If this gets enough attention, I will keep it updated with the game
## Anime Defenders AFK macro to reliably farm automatically

### Uses techniques such as reading Roblox memory without modifying it and optical character recognition to automate the game

## Features
* Automatically start and initialize all clients using Roblox Account Manager webserver
* Can farm the following game modes on all maps:
  * Story Mode (except Magma Cave and Underwater City)
  * Infinite Mode
  * Portals (except Golden Knight Portals)
  * Tower of Eternity (can be buggy)
  * Athenyx Realm Infinite (can be buggy)
* Reliably go to the same position on the map when placing for consistent farming
* Occasionally send screenshots to a Discord webhook for monitoring
* Custom sequence that lets you place, upgrade, sell, and more in any order you want

## Requirements
* [Tesseract OCR](https://github.com/tesseract-ocr/tesseract): [Download](https://github.com/UB-Mannheim/tesseract/releases/download/v5.4.0.20240606/tesseract-ocr-w64-setup-5.4.0.20240606.exe)
* [ViGEmBus](https://github.com/nefarius/ViGEmBus): [Download](https://github.com/nefarius/ViGEmBus/releases/download/v1.22.0/ViGEmBus_1.22.0_x64_x86_arm64.exe)
  * Should automatically install when installing requirements from source, but if it breaks then try reinstalling from here
  * You must manually install this if you are using the executable
* [Roblox Account Manager](https://github.com/Campionnn/Roblox-Account-Manager): [Download](https://github.com/Campionnn/Roblox-Account-Manager/releases/download/3.6.2/Roblox.Account.Manager.exe)
  * This links to my fork of the official RAM because there were some bugs in the webserver code that causes it to not work sometimes. These changes have been merged on the [official RAM](https://github.com/ic3w0lf22/Roblox-Account-Manager/pull/413), but are not included in the executable in releases for some reason
  * When asked to update check "Do not ask again" and click "No"

## Settings
Make sure the following are true for all accounts  
### Roblox
* Fullscreen is enabled and automatically opens in fullscreen
* Chat is closed
* Camera Mode is set to "Default (Classic)"
* UI Navigation Toggle is enabled
* Graphics settings are set to the lowest
* Language is set to English

### Anime Defenders
* Skill VFX is disabled
* Unit Info Position is set to Left
* Auto Skip Wave is enabled
* Low Quality Mode is enabled
* Damage Indicators are disabled
* Have the appropriate level that you want to farm unlocked
* Auto Max Speed can be enabled but might make early game less reliable
  * The script will automatically increase the speed based on the configs in `config.toml` if it is disabled

### Roblox Account Manager
* All accounts are added and logged in
* Multi Roblox is enabled
* Enable Web Server is enabled
* A port is set for the web server and is in `config.toml`
* Allow LaunchAccount Method is enabled

### Miscellaneous
* All instances of Roblox must be on the primary monitor or only have 1 monitor turned on
* This has only been extensively tested on 1920x1080 and 2560x1440 resolutions and may not work consistently on other resolutions
* Everything in `config.toml` is filled out. Optional settings are marked

## Step-by-step guide for first time users
1. Download and install the required software from [Requirements](#requirements)
   1. **Make sure you are using my fork of Roblox Account Manager, the official one has bugs that cause it to not work sometimes. The link can be found above**
   2. When asked to update RAM check "Do not ask again" and click "No"
   3. Choose any encryption method
   4. If you don't install Tesseract OCR in the default location, you will have to modify `config.toml` later
2. Add all accounts to Roblox Account Manager by clicking the `Add Account` button and logging in
3. Make sure the settings in [Roblox Account Manager Settings](#roblox-account-manager) are correct
4. Roblox Account Manager should be running whenever you want to use ADFK
5. Download the executable from the [latest release](https://github.com/Campionnn/ADFK/releases/latest)
6. Put the executable in its own folder
7. Run the executable once to generate `config.toml` and close it
8. Fill out necessary information in `config.toml`. Open `config.toml` in any text editor such as Notepad or [Notepad++](https://notepad-plus-plus.org/downloads/)
   1. Optional settings are marked
   2. Read the comment (the lines that start with #) above each setting to understand what they do and how to format them
   3. Set a port for the web server in Roblox Account Manager which can be any 4 numbers and put it in `config.toml` under `port`
   4. Add usernames from Roblox Account Manager to `config.toml` under `usernames`
      1. Make sure that these are usernames and not display names
      2. Each username should be in quotes and separated by a comma
      3. Square brackets surround the list of usernames
      4. Example: `usernames = ["username1", "username2", "username3"]`
      5. You can use any number of usernames from 1 to 4
   5. If you add a password to RAM webserver, you must add it to `config.toml` under `password`
   6. **Do the following steps if your private server link does not end in `privateServerLinkCode=12345678901234567890123456789012` with a bunch of random numbers**
      1. Open your private server link in a browser where you are logged into Roblox
      2. Wait for Roblox to launch and close the game
      3. Copy the new link from the browser and paste it into `config.toml` under `private_server_link`
   7. To create a Discord webhook, follow these instructions
      1. Go to a private Discord server that you have permission to create webhooks in
      2. Right-click on a channel and click `Edit Channel`
      3. Go to `Integrations` and click `Webhooks`
      4. Click `New Webhook` and optionally change the name and icon
      5. Copy the webhook URL and paste it into `config.toml` under `discord_webhook`
9. Manually open up every account one at a time and make sure every setting in [Settings](#settings) is correct
10. Run the executable again
11. Follow the instructions in the console to start the script
12. Information about `Roblox PIDs` and `custom sequences` can be found in the [Wiki (soon<sup>tm</sup>)](https://github.com/Campionnn/ADFK/wiki)

## Running from executable
1. Download the latest release from the [releases page](https://github.com/Campionnn/ADFK/releases/latest)
2. Put the executable in a folder
3. Run the executable once to generate `config.toml` 
4. Fill out necessary information in `config.toml`
5. Run the executable again

## Running from source
1. Install Python 3.11 or higher (3.11.4 recommended)
2. Install the required packages with `pip install -r requirements.txt` or running the script which will install them for you
3. Install Tesseract OCR from above
4. Optionally delete the precompiled memory_search.cp311-win_amd64.pyd file to automatically recompile yourself
5. You will likely have to do step 4 if you aren't using Python 3.11.4
6. Modify `config.toml` to your settings
7. Run the script with `python main.py`