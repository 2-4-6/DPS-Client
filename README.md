# Daymar Positioning System
Navigation tool, designed for route plotting during Daymar Rally, within the game Star Citizen by Cloud Imperium Games.
The client obtains 3D Coordinate data from ingame using the "/showlocation" command. 
The coordinate data is sent to our server where the data is calculated into latitude and longitude values and plotted on the [Daymar Positioning System site](https://daymar-positioning-system.vercel.app/) and displayed when the corresponding "run id" is entered.

## Download
The client can be downloaded [here](https://github.com/2-4-6/DPS-Client/releases).
Or if you wish to compile the source code yourself:
```
pyinstaller --onefile --noconsole --icon="Malney-Icon.ico" --uac-admin --add-data "MB-White.png;." .\DPS.py
```

## Usage
A login and password is required to use the client. This can be retrieved through the Discord bot.