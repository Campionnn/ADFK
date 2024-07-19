# ADFK

## Anime Defenders AFK macro to reliably farm automatically

Uses techniques such as reading Roblox memory without modifying it and optical character recognition to automate the game

### Requirements
* [Tesseract OCR](https://github.com/tesseract-ocr/tesseract): [Download](https://github.com/UB-Mannheim/tesseract/releases/download/v5.4.0.20240606/tesseract-ocr-w64-setup-5.4.0.20240606.exe)
* [ViGEmBus](https://github.com/nefarius/ViGEmBus): [Download](https://github.com/nefarius/ViGEmBus/releases/download/v1.22.0/ViGEmBus_1.22.0_x64_x86_arm64.exe)
  * Should automatically install when installing requirements, but if it breaks then try reinstalling from here

### Usage
Make sure the following are true for all accounts  
Roblox Settings:
* Fullscreen is enabled (F11 or toggle in settings)
* Chat is closed
* Camera Mode is set to "Default (Classic)"
* UI Navigation Toggle is enabled
* Graphics settings are set to the lowest

Anime Defenders Settings
* Skill VFX is disabled
* Unit Info Position is set to Left
* Auto Skip Wave is enabled
* Low Quality mode is enabled
* Have the appropriate level that you want to farm unlocked

Miscellaneous
* All instances of Roblox must be on the primary monitor or only have 1 monitor turned on

### Running from source
1. Install Python 3.8 or higher
2. Install the required packages with `pip install -r requirements.txt`
3. Install Tesseract OCR from above
4. Optionally delete the precompiled memory_search.cp311-win_amd64.pyd file to automatically recompile yourself
5. You will likely have to do step 4 if you aren't using python 3.11.4
6. Run the script with `python main.py`