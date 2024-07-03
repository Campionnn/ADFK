# In game roblox coords for internal use. Do not modify this file unless you know what you are doing.
# Change your own settings in config.py

init_pos1 = 13.1508  # y coord at leaderboard fast travel
init_tolerance1 = 0.0005
init_pos2 = -10.0  # y coord inside afk area
init_tolerance2 = 8.0

# Screen Key Sequence
# Sequence required to get to button after pressing UI Navigation Toggle
# X button to close intro screen
intro_sequence = "d"*50
# Fast travel button
fast_travel_sequence = "d"
# AFK fast travel button
afk_sequence = "d" + "s"
# Leaderboard fast travel button
leaderboard_sequence = "d" + "s"*3
# Story fast travel button
story_sequence = "d" + "s"*7
# Teleport after clicking afk
teleport_sequence = "s"*3 + "d"*2
# Leave & claim rewards button in afk area
leave_afk_sequence = "s"*3
# Claim button in afk area after clicking leave
claim_afk_sequence = "s" + "d"*2

# World you want to farm (Windmill Village)
world_sequence = "a" + "s"
# Infinite mode button
infinite_sequence = "s"*14
# Confirm button
confirm_sequence = "s"*16
# Start button
start_sequence = "d"*50 + "a"


# Roblox in game coordinates for lobby
story_play_pos = [-228.59048461914062, -269.32598876953125] # middle of story area
story_play_pos_tolerance = 2.0
story_enter_pos = [-259.55291748046875, -298.91363525390625]
story_enter_pos_tolerance = 5.0

# Roblox in game coordinates for story
story_place_pos = [-1666.4205322265625, -532.5964965820312]
story_place_pos_tolerance = 2.0
story_place_rot = 0
story_place_rot_tolerance = 2.0
