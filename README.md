# hl-bsp-viewer
Python program to parse .bsp files and do stuff with it.

With awful debug shader™ !!!
![awful shader](https://github.com/madghostek/hl-bsp-viewer/blob/main/debugview.png?raw=true)

## Requirements
use `pip install -r requirements.txt`

## Usage

run `BSPViewer.py -h` for help:

```
usage: BSPViewer.py [-h] [--entities [ENTITIES]] [--outpath [OUTPATH]] [--serialiser SERIALISER] [--display] filename

View BSP maps

positional arguments:
  filename              BSP map path

optional arguments:
  -h, --help            show this help message and exit
  --entities [ENTITIES], -e [ENTITIES]
                        exports entity bounding lines to display on server.
  --outpath [OUTPATH], -o [OUTPATH]
                        output path for entities. Supported formats: (json, csv)
  --serialiser SERIALISER, -s SERIALISER
                        force `outpath` format to something else
  --display, -d         show map in OpenGL window

examples: 

Shows the map in a window:
  python3 BSPViewer.py maps/de_dust2.bsp -d

Saves all trigger_push bounding edges to a json file:
  python3 BSPViewer.py maps/de_dust2.bsp -e trigger_push -o output.json

Saves all trigger_teleport bounding edges to a csv file with default name:
  python3 BSPViewer.py maps/de_dust2.bsp -e trigger_teleport -s csv
```

## Controls
* LMB and drag - rotate camera
* AWSD - move around
* QE - look to left/right
* up/down arrow - move up down
* ctrl+r - reset to origin
* ctrl-g - teleport to location (you need to run the script from some kind of console for that)
