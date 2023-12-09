from win32 import win32clipboard
import keyboard
import pyautogui
import pydirectinput
import PySimpleGUI as sg
import time
import threading
import requests
import re
from cryptography.fernet import Fernet
import datetime
import sys
import os

# Compile
# pyinstaller --onefile --noconsole --icon="Malney-Icon.ico" --uac-admin --add-data "MB-White.png;." .\DPS.py

TRIGGER_KEY = 'altgr'
ACTIVE_TRACKING = False
RUN_ID = ''
MAXIMUM_CHARACTER_LENGTH = 10
URL = 'https://navigation.mb-industries.co.uk/'

USERNAME = ""
API_KEY = ""
auth=(USERNAME, API_KEY)

encryption_key = b'jM4DlcXDBO6A91f4YjJ5_n7YBtf07eHdXrAXzQos7fI='

# Add resource path to include images into compiled exe
def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

def encrypt_data(data):
    cipher_suite = Fernet(encryption_key)
    encrypted_data = cipher_suite.encrypt(data.encode('utf-8'))
    return encrypted_data

def decrypt_data(encrypted_data):
    cipher_suite = Fernet(encryption_key)
    decrypted_data = cipher_suite.decrypt(encrypted_data).decode('utf-8')
    return decrypted_data

# Retrieve CSRF token
def get_token():
    token_url = URL + 'get_csrf_token/'
    response = requests.get(token_url)
    return response.json()['csrf_token']

# Verifies correct auth. Subsequent auth checks still apply, this just ensures correct details before proceeding
def login():
    try:
        url = URL + 'verify_user/'
        csrf_token = get_token()

        headers = {'X-CSRFToken': csrf_token}
        response = requests.post(url, headers=headers, auth=auth)
        # print(response.status_code)

        if response.status_code == 200:
            return True
        else:
            window['-HIDDEN_LOG-'].update(" Incorrect Login Details", text_color='red')
    except requests.exceptions.RequestException as e:
        window['-HIDDEN_LOG-'].update(f"Login Error: {e}", text_color='red')

# Sending coordinate data
def send_data(x_value, y_value, z_value, time):
    url = URL + 'postData/'
    csrf_token = get_token()

    encrypted_runID = encrypt_data(str(RUN_ID))
    encrypted_x = encrypt_data(str(x_value))
    encrypted_y = encrypt_data(str(y_value))
    encrypted_z = encrypt_data(str(z_value))
    encrypted_time = encrypt_data(str(time))

    payload = {
        "data": {
            "run_id": encrypted_runID.decode('utf-8'),
            "x": encrypted_x.decode('utf-8'),
            "y": encrypted_y.decode('utf-8'),
            "z": encrypted_z.decode('utf-8'),
            "time": encrypted_time.decode('utf-8')
        }
    }
    
    headers = {'X-CSRFToken': csrf_token}
    response = requests.post(url, json=payload, headers=headers, auth=auth)

    if response.status_code == 200:
        print("Data sent successfully to Django backend.")
    else:
        print(f"Failed to send data to Django backend. Status code: {response.status_code}")

# Delete last entry with a matching run ID
def delete_last():
    url = URL + 'deleteLast/'
    csrf_token = get_token()

    encrypted_runID = encrypt_data(str(RUN_ID))

    payload = {
        "data": {
            "run_id": encrypted_runID.decode('utf-8'),
        }
    }

    headers = {'X-CSRFToken': csrf_token,}
    response = requests.post(url, json=payload, headers=headers, auth=auth)

    if response.status_code == 200:
        print("Data sent successfully to Django backend.")
    else:
        print(f"Failed to send data to Django backend. Status code: {response.status_code}")

def get_runs(window):
    url = URL +'get_runs/'

    try: 
        response = requests.get(url, auth=auth)
        run_ids = response.json()
        
        run_ids_string = '\n'.join(run_ids)
        window['-HISTORY-'].update(run_ids_string)
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        window['-OUTPUT-'].update("Failed to Retrieve History", text_color='red')

def macro(e):
    if ACTIVE_TRACKING and e.event_type == keyboard.KEY_UP:
        time.sleep(0.05)
        pydirectinput.press('enter')
        pyautogui.typewrite('/showlocation')
        pydirectinput.press('enter')

        # SC saves coordinates directly to clipboard
        try:
            win32clipboard.OpenClipboard()
            coordinate_data = win32clipboard.GetClipboardData()
            win32clipboard.CloseClipboard()
        except Exception as e:
            window['-OUTPUT-'].update(f"Clipboard Error: {e}", text_color='red')

        # Example: /showlocation

        # Verify pattern of data
        pattern =  r"Coordinates: x:(-?\d+\.\d+) y:(-?\d+\.\d+) z:(-?\d+\.\d+)"
        match = re.search(pattern, coordinate_data)

        Reference_time_UTC = datetime.datetime(2020, 1, 1)
        Epoch = datetime.datetime(1970, 1, 1)
        Reference_time = (Reference_time_UTC - Epoch).total_seconds()

        try :
            import ntplib
            c = ntplib.NTPClient()
            response = c.request('europe.pool.ntp.org', version=3)
            server_time = response.tx_time
            time_offset = response.offset
        except Exception as e:
            window['-OUTPUT-'].update(f"NTP Request Error: {e}", text_color='red')
            time_offset = 0

        # print('Time_offset:', time_offset)

        New_time = time.time() + time_offset
        Time_passed_since_reference_in_seconds = New_time - Reference_time

        if match and RUN_ID:
            x_value = float(match.group(1))
            y_value = float(match.group(2))
            z_value = float(match.group(3))

            try:
                send_data(x_value, y_value, z_value, Time_passed_since_reference_in_seconds)

                window['-X-'].update(x_value)
                window['-Y-'].update(y_value)
                window['-Z-'].update(z_value)
                window['-OUTPUT-'].update("Coordinates sent successfully", text_color='green')
            except:
                window['-OUTPUT-'].update("Connection Failed", text_color='red')

        else:
            window['-OUTPUT-'].update("Failed to obtain Coordinate data", text_color='red')

# ---------------------------------------------------------------- Initiate Macro ----------------------------------------------------------------

macro_thread = threading.Thread(target=keyboard.on_release_key, args=(TRIGGER_KEY, macro))
macro_thread.daemon = True
macro_thread.start()

# ----------------------------------------------------------------Create the PySimpleGUI window----------------------------------------------------------------
sg.theme('Dark Blue 1')


# ----------------------------------------------------------------PySimpleGUI Login Layout----------------------------------------------------------------
login_layout = [
    [sg.Image(resource_path('MB-White.png'),
   expand_x=True, expand_y=True)],
    [sg.Text("Username", key='-USER-')],
    [sg.Input('', enable_events=True, key='-USERNAME-', font=('Arial Bold', 10), size=(40, 1), justification='left', background_color=sg.theme_text_color(), text_color='black')],
    [sg.Text("Key", key='-KEY-')],
    [sg.Input('', enable_events=True, key='-APIKEY-', font=('Arial Bold', 10), size=(40, 1), justification='left', background_color=sg.theme_text_color(), text_color='black', password_char='*')],
    [sg.Button('Show Password', key='-SHOWPASS-', font=('Arial Bold', 10)), sg.Button('Login', key='-LOGIN-', font=('Arial Bold', 10))],
    [sg.Text("", key='-HIDDEN_LOG-', visible=True)]
]

# ----------------------------------------------------------------PySimpleGUI Main Layout----------------------------------------------------------------
run_layout = [
    [
        sg.Input('', enable_events=True, key='-ID-', font=('Arial Bold', 10), size=(50, 1), justification='left', background_color=sg.theme_text_color(), text_color='black'),
        sg.Button('SET', key='-SET-', font=('Arial Bold', 10))
    ],
    [sg.Text("Run ID: "), sg.Text("Run ID not set", size=(30, 1), key='-RUN-')]
]

run_frame = sg.Frame('Run ID', run_layout, size=(440,80))

coord_layout = [
    [sg.Text("X: "), sg.Text("", size=(30, 1), key='-X-')],
    [sg.Text("Y: "), sg.Text("", size=(30, 1), key='-Y-')],
    [sg.Text("Z: "), sg.Text("", size=(30, 1), key='-Z-')]
]

coord_frame = sg.Frame('Coordinate Data', coord_layout)
t5 = sg.Text("Output: ", size=(6, 1)), sg.Text("", size=(45, 1), key='-OUTPUT-', background_color='black')

control_layout = [
    [
        sg.Button('UNDO LAST', key='-UNDO-', font=('Arial Bold', 10)),
        sg.Button('RELOAD HISTORY', key='-RELOAD-', font=('Arial Bold', 10)),
        sg.Button('ENABLE/DISABLE', key='-ACTIVATE-', font=('Arial Bold', 10)),
        sg.Text("INACTIVE", text_color='red', key='-STATUS-')
    ]
]

control_frame = sg.Frame('Controls', control_layout, size=(440,50))

history_layout = [
    [
        sg.Multiline(default_text='Reload History to view', size=(60, 10), key='-HISTORY-', autoscroll=True, enable_events=True, background_color='white', text_color='black')
    ]
]

history_frame = sg.Frame('Run History', history_layout, size=(141,100))

output_layout = [
    [
        sg.Text("", size=(52, 1), key='-OUTPUT-', background_color='black')
    ]

]

output_frame = sg.Frame('Console', output_layout, size=(440,50))

instruction_layout = [
    [
        sg.Text("RUN ID \n- To start a new run, \nenter a unique ID.\n- To continue a run,\nenter an existing ID\n\n"+
                "CONTROLS:\nUNDO LAST \ndeletes the last \ncoordinate input with \nthe matching Run ID\n"+
                "ENABLE/DISABLE\nActivates and \nDeactivates the \nkeybind"),

    ]
]

instruction_frame = sg.Frame('How to use: ', instruction_layout, size=(150,330))

main_layout = [[run_frame],
          [coord_frame, history_frame],
          [control_frame],
          [output_frame]]

main_frame = sg.Frame('Connection', main_layout, size=(460,330))

verified_layout = [[instruction_frame, main_frame]]

layout = [[sg.Column(login_layout, key='-COL1-'), 
           sg.Column(verified_layout, key='-COL2-', visible=False)]]

window = sg.Window("Daymar Positioning System (DPS)", layout, margins=(5, 5), icon='Malney-Icon.ico')

# ---------------------------------------------------------------- Event Handler ----------------------------------------------------------------
layout = 1
password = True

while True:
    event, values = window.read()
    if event == '-SHOWPASS-':
        password = not password
        password_char = '*' if password else ''
        window['-APIKEY-'].update(password_char=password_char)

    # Login and verify details
    if event == '-LOGIN-':
        USERNAME = values['-USERNAME-']
        API_KEY = values['-APIKEY-']
        auth=(USERNAME, API_KEY)
        # Verify API and user here
        if API_KEY and USERNAME and login():
        # if API_KEY and USERNAME:
            window[f'-COL{layout}-'].update(visible=False)
            layout += 1
            window[f'-COL{layout}-'].update(visible=True)

    #Setting Run ID
    if event == '-SET-':
        if values['-ID-'] != "" and len(values['-ID-']) < MAXIMUM_CHARACTER_LENGTH:
            RUN_ID = values['-ID-']
            window['-RUN-'].update(RUN_ID)
            window['-OUTPUT-'].update("Run ID set", text_color='green')
        elif len(values['-ID-']) >= MAXIMUM_CHARACTER_LENGTH:
            window['-OUTPUT-'].update("Exceeded Maximum Character Count (9)", text_color='red')
        else:
            window['-OUTPUT-'].update("Invalid Run ID", text_color='red')

    #Enable or disable tracking
    if event == '-ACTIVATE-':
        if ACTIVE_TRACKING == False:
            window['-STATUS-'].update("ACTIVE", text_color='green')
            ACTIVE_TRACKING = True
        elif ACTIVE_TRACKING == True:
            window['-STATUS-'].update("INACTIVE", text_color='red')
            ACTIVE_TRACKING = False

    if event == '-UNDO-':
        try:
            delete_last()
            window['-OUTPUT-'].update("Delete request sent", text_color='green')
        except:
            window['-OUTPUT-'].update("Failed to Delete", text_color='red')

    if event == '-RELOAD-':
        get_runs(window)

    if event == sg.WIN_CLOSED:
        break

keyboard.unhook_all()
macro_thread.join()
window.close()

# sg.theme_previewer()