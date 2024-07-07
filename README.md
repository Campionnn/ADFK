# ADFK

## Anime Defenders AFK macro to reliably farm automatically

Uses techniques such as reading Roblox memory without modifying it and optical character recognition to automate the game

### Requirements
* [Tesseract OCR](https://github.com/tesseract-ocr/tesseract): [Download](https://github.com/UB-Mannheim/tesseract/releases/download/v5.4.0.20240606/tesseract-ocr-w64-setup-5.4.0.20240606.exe)
* [ViGEmBus](https://github.com/nefarius/ViGEmBus): [Download](https://github.com/nefarius/ViGEmBus/releases/download/v1.22.0/ViGEmBus_1.22.0_x64_x86_arm64.exe)
  * Should automatically download when installing requirements, but if it breaks then try reinstalling from here

### Usage
Make sure the following are true for all accounts:
* Roblox is set to fullscreen (no title bar showing) and will always launch this way
* Camera Mode is set to Default (Classic)
* UI Navigation Toggle is enabled
* Chat is closed
* Skill VFX is disabled
* Unit Info Position is set to Left
* Auto Skip Wave is enabled
* Optionally turn on Low Quality mode and turn graphics all the way down
* Have the appropriate level that you want to farm unlocked

#### Running from source
1. Install Python 3.8 or higher
2. Install the required packages with `pip install -r requirements.txt`
3. Install Tesseract OCR from above
4. Optionally delete the precompiled memory_search.cp311-win_amd64.pyd file to automatically recompile yourself
5. Run the script with `python main.py`