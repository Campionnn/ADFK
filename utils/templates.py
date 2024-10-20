config_template = r"""
# ADFK Settings

# Kill key ex: "del" or "esc"
kill_key = "del"
# How much logging you want ex: "info" or "debug"
logging_level = "debug"
# Tesseract OCR Path. Default Location: "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
# Double backslashes or single forwardslashes are required
tesseract_path = "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
# Which wave to stop at and leave the game during infinite(-1 to go until death) ex: 31
wave_stop = 31
# What speed to make the game for main account ex: 1, 2, 3
speed_main = 2
# Default speed for accounts that are not main account ex: 1, 2, 3
speed_default = 2
# Whether Auto Max Speed is enabled. Won't click the speed-up buttons if enabled ex: true or false
auto_max_speed = false
# Discord webhook link that occasionally sends screenshots of the game
discord_webhook = "" # Optional
# Screenshot quality from 1-100. Lower numbers means less quality ex: 50
screenshot_quality = 50

# Next 3 settings are only used when not using a custom sequence
# Tower hotkey that you want main account to use ex: "1"
tower_hotkey = "1"
# Tower cap for the tower above ex: 3
tower_cap = 5
# How much the tower costs to place ex: 850
tower_cost = 500


# Roblox Account Manager (RAM) Settings
# Must enable the following settings in RAM: Multi Roblox, Enable Web Server, Allow LaunchAccount Method

# Webserver Port for RAM ex: 8080
port = 8080
# Webserver Password for RAM. Leave blank if you didn't set one ex: "1234567890abcdef"
password = "" # Optional
# List of usernames (not display names) in RAM ex: ["username1", "username2"] first username in list is used as main account
# Double quotes around each username
usernames = []
# Link to private server ex: "https://www.roblox.com/games/17017769292/Anime-Defenders?privateServerLinkCode=12345678901234567890123456789012"
# If it does not end in all numbers, open private server link in a browser and copy the code from the url once it changes
private_server_link = ""

# Config version, do not modify
config_version = "v1"
"""
