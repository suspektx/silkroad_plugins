#   This plugin requires several external libraries
#   You have to have these files in phBot/Plugins/python38/Lib
#   Otherwise the plugin will not load
#
#   certifi
#   charset_normalizer
#   gtts
#   idna
#   playsound
#   requests
#   urllib3
#

import os
import QtBind
import struct
import re
import json
import threading
import time
import urllib.request

from phBot import *
from gtts import gTTS
from playsound import playsound
from threading import Timer

# GLOBAL VARIABLES
plugin_name = 'Custom Alarms'
plugin_version = '1.2'
plugin_new_version = 0

job_list = ["Selket", "Neith", "Isis", "Anubis", "Haroeris", "Seth"]

custom_flags = ["__mute__"]
mute_flag = False

last_alarm_timestamps = {}

# PATH DECLARATIONS
config_folder = os.path.join(get_config_dir(), "[custom_alarms]")
alarm_folder = os.path.join(config_folder, "[custom_alarms]")

# CONFIG HANDLING
def get_character_config():
    server_name = get_character_data()['server']
    character_name = get_character_data()['name']
    config_name = f'[{server_name}]_{character_name}.json'

    return os.path.join(config_folder, config_name)

def load_config():
    global custom_flags

    try:
        with open(get_character_config(), "r+") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}

    modified = False

    for flag in custom_flags:
        if flag not in data:
            default_value = False
            data[flag] = default_value
            log(f'{flag} flag was created and set as {default_value} by default.')
            modified = True

    if modified:
        save_config(data)
    
    return data

def save_config(data):
    preserved_flags = {flag: data.pop(flag, False) for flag in custom_flags}
    sorted_data = {flag: preserved_flags[flag] for flag in custom_flags}
    sorted_data.update(dict(sorted(data.items())))

    with open(get_character_config(), 'w+') as file:
        json.dump(sorted_data, file, indent=4)

def add_unique_to_json(unique_name, status):
    data = load_config()
    data[unique_name] = status

    save_config(data)

def remove_unique_from_json(unique_name):
    data = load_config()

    if unique_name in data:
        del data[unique_name]

        save_config(data)

def toggle_unique_status(unique_name):
    data = load_config()

    if unique_name in data:
        data[unique_name] = not data[unique_name]

    save_config(data)

# GUI
gui = QtBind.init(__name__, plugin_name)
plugin_label = QtBind.createLabel(gui, "Enjoy! made by suspekt.", 6, 0)
description_label = QtBind.createLabel(gui, "Custom alarm system using TTS.", 6, 35)

unique_label = QtBind.createLabel(gui, "Possible Uniques", 70, 65)
unique_list = QtBind.createList(gui, 20, 80, 185, 190)

add_unique_to_list = QtBind.createButton(gui, 'add_unique_alarm_clicked', "            \n►\n            ", 230, 125)
remove_unique_from_list = QtBind.createButton(gui, 'remove_unique_alarm_clicked', "            \n◄\n            ", 230, 175)

alarm_label = QtBind.createLabel(gui, "Unique Alarm List", 350, 35)
add_unique_textbox = QtBind.createLineEdit(gui, '', 300, 55, 125, 20)
manual_add_unique_button = QtBind.createButton(gui, 'manual_add_unique_alarm_clicked', "       +       ", 430, 57)
manual_delete_unique_button = QtBind.createButton(gui, 'manual_delete_unique_alarm_clicked', "    Delete unique from alarm list   ", 315, 275)
unique_alarm_list = QtBind.createList(gui, 300, 80, 185, 190)

__mute__ = QtBind.createCheckBox(gui, "mute_checked", "Mute alarms", 500, 80)

# GUI FUNCTIONS
def load_gui():
    global mute_flag
    
    if os.path.exists(get_character_config()):
        QtBind.clear(gui, add_unique_textbox)
        QtBind.clear(gui, unique_list)
        QtBind.clear(gui, unique_alarm_list)

        data = load_config()

        for unique_name, status in data.items():
            if unique_name in custom_flags:
                checkbox = globals().get(unique_name)
                QtBind.setChecked(gui, checkbox, status)
                if status == True:
                     mute_flag = True
            elif status:
                QtBind.append(gui, unique_alarm_list, unique_name)
            else:
                QtBind.append(gui, unique_list, unique_name)

# FLAG HANDLING
def mute_checked(checked):
    global mute_flag
    
    if checked:
        mute_flag = True
        toggle_unique_status("__mute__")
        log("Alarms muted.")
    else:
        mute_flag = False
        toggle_unique_status("__mute__")
        log("Alarms unmuted.")

# LIST HANDLING
def manual_add_unique_alarm_clicked():
    unique_name = QtBind.text(gui, add_unique_textbox)

    if ensure_no_duplicates(unique_name, unique_alarm_list):
        QtBind.append(gui, unique_alarm_list, unique_name)
        ensure_alphabetical_order(unique_alarm_list)

    QtBind.clear(gui, add_unique_textbox)

def manual_delete_unique_alarm_clicked():
    index = QtBind.currentIndex(gui, unique_alarm_list)
    unique_name = QtBind.text(gui, unique_alarm_list)

    QtBind.removeAt(gui, unique_alarm_list, index)
    remove_unique_from_json(unique_name)

    if unique_name.strip():
        log(f'[{unique_name}] deleted sucessfuly.')
    else:
        log('You can only delete uniques from the alarm list.')

def add_unique_alarm_clicked():
    unique_name = QtBind.text(gui, unique_list)

    if unique_name.strip():
        index = QtBind.currentIndex(gui, unique_list)
        QtBind.removeAt(gui, unique_list, index)

        QtBind.append(gui, unique_alarm_list, unique_name)
        ensure_alphabetical_order(unique_alarm_list)
        toggle_unique_status(unique_name)

        log(f'[{unique_name}] added to alarm list.')

def remove_unique_alarm_clicked():
    unique_name = QtBind.text(gui, unique_alarm_list)

    if unique_name.strip():
        index = QtBind.currentIndex(gui, unique_alarm_list)
        QtBind.removeAt(gui, unique_alarm_list, index)

        QtBind.append(gui, unique_list, unique_name)
        ensure_alphabetical_order(unique_list)
        toggle_unique_status(unique_name)

        log(f'[{unique_name}] removed from alarm list.')


# LIST FUNCTIONS
def ensure_alphabetical_order(list):
    current_items = QtBind.getItems(gui, list)

    if current_items == sorted(current_items):
            return True
    else:
        current_items = sorted(current_items)
        update_list(list, current_items)

def ensure_no_duplicates(unique_name, list):
    items_unique_list = QtBind.getItems(gui, unique_list)
    items_unique_alarm_list = QtBind.getItems(gui, unique_alarm_list)

    if unique_name not in items_unique_list and unique_name not in items_unique_alarm_list:
        if list == unique_list:
            log(f'[{unique_name}] was added to the list of possible uniques.')
            add_unique_to_json(unique_name, False)
        elif list == unique_alarm_list:
            log(f'[{unique_name}] was added to the alarm list.')
            add_unique_to_json(unique_name, True)
        return True
    else:
        if list == unique_alarm_list and unique_name in items_unique_list:
            log(f'[{unique_name}] already exists in possible uniques, grab it from there.')
        return False

def update_list(list, ordered_items):
    QtBind.clear(gui, list)

    for items in ordered_items:
        QtBind.append(gui, list, items)

# ALARM FUNCTIONS
def create_alarm(unique_name):
    language = 'en'
    alarm = gTTS(text=unique_name, lang=language, slow=True) 
    alarm_path = os.path.join(alarm_folder, f'{unique_name}.mp3')

    alarm.save(alarm_path) 
    log(f'Alarm file for [{unique_name}] created.')
    play_alarm(unique_name)

def play_alarm(unique_name):
    global last_alarm_timestamps
    
    alarm_path = os.path.join(alarm_folder, f'{unique_name}.mp3')
    
    current_time = time.time()
    last_alarm_time = last_alarm_timestamps.get(unique_name, 0)
    cooldown_duration = 5  # Adjust this duration as needed (in seconds)

    if current_time - last_alarm_time >= cooldown_duration:
        if os.path.exists(alarm_path):
            threading.Thread(target=playsound.playsound, args=(alarm_path,)).start()
        else:
            create_alarm(unique_name)

        last_alarm_timestamps[unique_name] = current_time

# BUILT-IN FUNCTIONS
def handle_joymax(opcode, data):
    if opcode == 0x300C:
        update_type = data[0]

        if update_type in [5, 6]:
            model_id = struct.unpack_from('<I', data, 2)[0]
            unique_name = get_monster(int(model_id))['name']
            unique_name = unique_name.strip()

            if "(Titan)" in unique_name:
                unique_name = "(Titan Uniques)"
            elif unique_name in job_list:
                unique_name = "(Job Uniques)"

            items_unique_alarm_list = QtBind.getItems(gui, unique_alarm_list)

            if ensure_no_duplicates(unique_name, unique_list):
                QtBind.append(gui, unique_list, unique_name)
                ensure_alphabetical_order(unique_list)
                    
            if update_type == 5 and unique_name in items_unique_alarm_list and not mute_flag:
                play_alarm(unique_name)

    return True

def joined_game():
	Timer(4.0, load_gui, ()).start()

# RELOAD PLUGIN SUPPORT AND CONFIG FOLDER CREATION
if not os.path.exists(config_folder):
    os.makedirs(config_folder)
    log(f'[{plugin_name}] v.{plugin_version} ~ config folder created.')

if not os.path.exists(alarm_folder):
    os.makedirs(alarm_folder)
    log(f'[{plugin_name}] v.{plugin_version} ~ alarm folder created.')

# UPDATE CHECK
def update_check():
	global plugin_new_version
	#avoid request spam
	if plugin_new_version == 0:
		try:
			req = urllib.request.Request('https://raw.githubusercontent.com/suspektx/silkroad_plugins/main/custom_alarms/custom_alarms.py', headers={'User-Agent': 'Mozilla/5.0'})
			with urllib.request.urlopen(req) as f:
				lines = str(f.read().decode("utf-8")).split()
				for num, line in enumerate(lines):
					if line == 'version':
						plugin_new_version = int(lines[num+2].replace(".",""))
						plugin_current_version = int(str(plugin_version).replace(".",""))
						if plugin_new_version > plugin_current_version:
							log(f'[{plugin_name}] has an update available.')
		except:
			pass

# PLUGIN LOAD
update_check()
Timer(1.0, load_gui, ()).start()
log(f'[{plugin_name}] v.{plugin_version} ~ loaded.')