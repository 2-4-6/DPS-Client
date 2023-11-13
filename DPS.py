import win32clipboard
import keyboard
import json
import pyautogui
import pydirectinput
import PySimpleGUI as sg
import time
import threading
import requests
import re
from cryptography.fernet import Fernet

TRIGGER_KEY = 'altgr'
ACTIVE_TRACKING = False
USER_ID = ''


encryption_key = b'jM4DlcXDBO6A91f4YjJ5_n7YBtf07eHdXrAXzQos7fI='

def encrypt_data(data):
    cipher_suite = Fernet(encryption_key)
    encrypted_data = cipher_suite.encrypt(data.encode('utf-8'))
    return encrypted_data

def decrypt_data(encrypted_data):
    cipher_suite = Fernet(encryption_key)
    decrypted_data = cipher_suite.decrypt(encrypted_data).decode('utf-8')
    return decrypted_data

def send_data(x_value, y_value, z_value):
    url = 'http://127.0.0.1:8000/postData/'

    encrypted_x = encrypt_data(str(x_value))
    encrypted_y = encrypt_data(str(y_value))
    encrypted_z = encrypt_data(str(z_value))

    payload = {
        "data": {
            "x": encrypted_x.decode('utf-8'),
            "y": encrypted_y.decode('utf-8'),
            "z": encrypted_z.decode('utf-8')
        }
    }

    response = requests.post(url, json=payload)

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

        # Example: Coordinates: x:-19022732572.526512 y:-2613335409.721847 z:-2096.384425
        # Verify pattern of data
        pattern =  r"Coordinates: x:(-?\d+\.\d+) y:(-?\d+\.\d+) z:(-?\d+\.\d+)"
        match = re.search(pattern, coordinate_data)

        if match:
            x_value = float(match.group(1))
            y_value = float(match.group(2))
            z_value = float(match.group(3))
       
            send_data(x_value, y_value, z_value)

            window['-X-'].update(x_value)
            window['-Y-'].update(y_value)
            window['-Z-'].update(z_value)
            window['-OUTPUT-'].update("Coordinates sent successfully")

        else:
            window['-OUTPUT-'].update("Failed to obtain Coordinate data", text_color='red')

# Macro in separate thread
macro_thread = threading.Thread(target=keyboard.on_release_key, args=(TRIGGER_KEY, macro))
macro_thread.daemon = True
macro_thread.start()

# Create the PySimpleGUI window
t0 = sg.Text("Run ID", )
i1 = sg.Input('', enable_events=True, key='-ID-', font=('Arial Bold', 10), expand_x=True, justification='left')
b1 = sg.Button('SET', key='-SET-', font=('Arial Bold', 10))
t0_1 = sg.Text("Run ID: "), sg.Text("Run ID not set", size=(30, 1), key='-USER-')
t1 = sg.Text("Coordinate Data", font=('Arial Bold', 12))
t2 = sg.Text("X: "), sg.Text("", size=(30, 1), key='-X-')
t3 = sg.Text("Y: "), sg.Text("", size=(30, 1), key='-Y-')
t4 = sg.Text("Z: "), sg.Text("", size=(30, 1), key='-Z-')
t5 = sg.Text("Output: "), sg.Text("", size=(30, 1), key='-OUTPUT-')
b2 = sg.Button('ENABLE/DISABLE', key='-ACTIVATE-', font=('Arial Bold', 10))
t6 = sg.Text("INACTIVE", text_color='red', key='-STATUS-')

layout = [[t0, i1, b1],[t0_1],[t1],[t2],[t3],[t4],[b2, t6],[t5]]

window = sg.Window("Daymar Positioning Service (DPS)", layout, margins=(100, 50))

# Create an event loop
while True:
    event, values = window.read()

    #Setting user ID
    if event == '-SET-':
        if values['-ID-'] != "":
            USER_ID = values['-ID-']
            window['-USER-'].update(USER_ID)
            window['-OUTPUT-'].update("User ID set", text_color='green')
        else:
            window['-OUTPUT-'].update("Invalid User ID", text_color='red')

    #Enable or disable tracking

    if event == '-ACTIVATE-':
        if ACTIVE_TRACKING == False:
            window['-STATUS-'].update("ACTIVE", text_color='green')
            ACTIVE_TRACKING = True
        elif ACTIVE_TRACKING == True:
            window['-STATUS-'].update("INACTIVE", text_color='red')
            ACTIVE_TRACKING = False


    if event == sg.WIN_CLOSED:
        break

keyboard.unhook_all()
macro_thread.join()
window.close()

# sg.theme_previewer()
