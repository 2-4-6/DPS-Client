import win32clipboard
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

TRIGGER_KEY = 'altgr'
ACTIVE_TRACKING = False
RUN_ID = ''
MAXIMUM_CHARACTER_LENGTH = 10


encryption_key = b'jM4DlcXDBO6A91f4YjJ5_n7YBtf07eHdXrAXzQos7fI='

def encrypt_data(data):
    cipher_suite = Fernet(encryption_key)
    encrypted_data = cipher_suite.encrypt(data.encode('utf-8'))
    return encrypted_data

def decrypt_data(encrypted_data):
    cipher_suite = Fernet(encryption_key)
    decrypted_data = cipher_suite.decrypt(encrypted_data).decode('utf-8')
    return decrypted_data

def get_token():
    token_url = 'http://127.0.0.1:8000/get_csrf_token/'
    response = requests.get(token_url)
    return response.json()['csrf_token']

def send_data(x_value, y_value, z_value, time):
    url = 'http://127.0.0.1:8000/postData/'
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
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        print("Data sent successfully to Django backend.")
    else:
        print(f"Failed to send data to Django backend. Status code: {response.status_code}")

def delete_last():
    url = 'http://127.0.0.1:8000/deleteLast/'
    csrf_token = get_token()

    encrypted_runID = encrypt_data(str(RUN_ID))

    payload = {
        "data": {
            "run_id": encrypted_runID.decode('utf-8'),
        }
    }

    headers = {'X-CSRFToken': csrf_token}
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        print("Data sent successfully to Django backend.")
    else:
        print(f"Failed to send data to Django backend. Status code: {response.status_code}")

def macro(e):
    if ACTIVE_TRACKING and e.event_type == keyboard.KEY_UP:
        time.sleep(0.05)
        pydirectinput.press('enter')
        pyautogui.typewrite('/showlocation')
        pydirectinput.press('enter')

        # SC saves coordinates directly to clipboard
        win32clipboard.OpenClipboard()
        coordinate_data = win32clipboard.GetClipboardData()
        win32clipboard.CloseClipboard()

        # Example: Coordinates: x:-18930720609.852791 y:-2610232694.427539 z:221270.571209
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
        except:
            print("Error: Could not get time from NTP server")
            sys.stdout.flush()
            time_offset = 0

        # print('Time_offset:', time_offset)

        New_time = time.time() + time_offset
        Time_passed_since_reference_in_seconds = New_time - Reference_time

        if match and RUN_ID:
            x_value = float(match.group(1))
            y_value = float(match.group(2))
            z_value = float(match.group(3))
       
            send_data(x_value, y_value, z_value, Time_passed_since_reference_in_seconds)

            window['-X-'].update(x_value)
            window['-Y-'].update(y_value)
            window['-Z-'].update(z_value)
            window['-OUTPUT-'].update("Coordinates sent successfully", text_color='green')

        else:
            window['-OUTPUT-'].update("Failed to obtain Coordinate data", text_color='red')

# Macro in separate thread
macro_thread = threading.Thread(target=keyboard.on_release_key, args=(TRIGGER_KEY, macro))
macro_thread.daemon = True
macro_thread.start()

# Create the PySimpleGUI window
sg.theme('Dark Blue 1')

t0 = sg.Text("Run ID", )
i1 = sg.Input('', enable_events=True, key='-ID-', font=('Arial Bold', 10), expand_x=True, justification='left', background_color=sg.theme_text_color(), text_color='black')
b1 = sg.Button('SET', key='-SET-', font=('Arial Bold', 10))
t0_1 = sg.Text("Run ID: "), sg.Text("Run ID not set", size=(30, 1), key='-RUN-')
t1 = sg.Text("Coordinate Data", font=('Arial Bold', 12))
t2 = sg.Text("X: "), sg.Text("", size=(30, 1), key='-X-')
t3 = sg.Text("Y: "), sg.Text("", size=(30, 1), key='-Y-')
t4 = sg.Text("Z: "), sg.Text("", size=(30, 1), key='-Z-')
t5 = sg.Text("Output: "), sg.Text("", size=(30, 1), key='-OUTPUT-', background_color='black')
b2 = sg.Button('ENABLE/DISABLE', key='-ACTIVATE-', font=('Arial Bold', 10))
t6 = sg.Text("INACTIVE", text_color='red', key='-STATUS-')
b3 = sg.Button('UNDO LAST', key='-UNDO-', font=('Arial Bold', 10))

layout = [[t0, i1, b1],[t0_1],[t1],[t2],[t3],[t4],[b3, b2, t6],[t5]]

window = sg.Window("Daymar Positioning Service (DPS)", layout, margins=(100, 50))

# Create an event loop
while True:
    event, values = window.read()

    #Setting Run ID
    if event == '-SET-':
        if values['-ID-'] != "" and len(values['-ID-']) < MAXIMUM_CHARACTER_LENGTH:
            RUN_ID = values['-ID-']
            window['-RUN-'].update(RUN_ID)
            window['-OUTPUT-'].update("Run ID set", text_color='green')
        elif len(values['-ID-']) >= MAXIMUM_CHARACTER_LENGTH:
            window['-OUTPUT-'].update("Exceeded Max Character", text_color='red')
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
        delete_last()
        window['-OUTPUT-'].update("i havent worked on this yet", text_color='green')

    if event == sg.WIN_CLOSED:
        break

keyboard.unhook_all()
macro_thread.join()
window.close()

# sg.theme_previewer()