# ADFK

## IMPORTANT: This was last updated right before they added the unit manager QoL feature, it still mostly works but it can break in certain circumstances. The new golden portals have not been added either
## If this gets enough attention, I will keep it updated with the game
## Anime Defenders AFK macro to reliably farm automatically

Uses techniques such as reading Roblox memory without modifying it and optical character recognition to automate the game

### Features
* Automatically start and initialize all clients using Roblox Account Manager webserver
* Can farm the following game modes on all maps:
  * Story Mode
  * Infinite Mode
  * Portals (except golden portals)
  * Tower of Eternity (can be buggy)
  * Athenyx Realm Infinite (can be buggy)
* Reliably go to the same position on the map when placing for consistent farming
* Occasionally send screenshots to a Discord webhook for monitoring
* Custom sequence that lets you place, upgrade, sell, and more in any order you want

### Requirements
* [Tesseract OCR](https://github.com/tesseract-ocr/tesseract): [Download](https://github.com/UB-Mannheim/tesseract/releases/download/v5.4.0.20240606/tesseract-ocr-w64-setup-5.4.0.20240606.exe)
* [ViGEmBus](https://github.com/nefarius/ViGEmBus): [Download](https://github.com/nefarius/ViGEmBus/releases/download/v1.22.0/ViGEmBus_1.22.0_x64_x86_arm64.exe)
  * Should automatically install when installing requirements, but if it breaks then try reinstalling from here
* [Roblox Account Manager](https://github.com/Campionnn/Roblox-Account-Manager): [Download](https://github.com/Campionnn/Roblox-Account-Manager/releases/tag/3.6.2)
  * This links to my fork of the official RAM because there were some bugs in the webserver code that caused it to not work sometimes. These changes have been merged on the [official RAM](https://github.com/ic3w0lf22/Roblox-Account-Manager/pull/413), but are not included in the executable in releases for some reason

### Usage
Make sure the following are true for all accounts  
Roblox Settings:
* Fullscreen is enabled (F11 or toggle in settings)
* Chat is closed
* Camera Mode is set to "Default (Classic)"
* UI Navigation Toggle is enabled
* Graphics settings are set to the lowest
* Language is set to English

Anime Defenders Settings
* Skill VFX is disabled
* Unit Info Position is set to Left
* Auto Skip Wave is enabled
* Low Quality mode is enabled
* Have the appropriate level that you want to farm unlocked

Miscellaneous
* All instances of Roblox must be on the primary monitor or only have 1 monitor turned on
* This has only been extensively tested on 1920x1080 and 2560x1440 resolutions and may not work on other resolutions
* All accounts are added to Roblox Account Manager
* Everything in `config.toml` is filled out. Discord webhook and webserver password are optional

### Running from executable(Recommended for most users)
1. Download the latest release from the [releases page](https://github.com/Campionnn/ADFK/releases)
2. Put the executable in a folder
3. Run the executable once to generate the `config.toml` file 
4. Fill out necessary information in `config.toml`
5. Run the executable again

### Running from source
1. Install Python 3.8 or higher (3.11.4 recommended)
2. Install the required packages with `pip install -r requirements.txt` or running the script which will install them for you
3. Install Tesseract OCR from above
4. Optionally delete the precompiled memory_search.cp311-win_amd64.pyd file to automatically recompile yourself
5. You will likely have to do step 4 if you aren't using Python 3.11.4
6. Modify the `config.toml` file to your settings
7. Run the script with `python main.py`
