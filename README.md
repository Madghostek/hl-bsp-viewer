# hl-bsp-viewer
Python program to parse .bsp files and do stuff with it.

With awful debug shader™ !!!
![awful shader](https://github.com/madghostek/hl-bsp-viewer/blob/main/debugview.png?raw=true)

## Requirements
use `pip unfreeze requirements.txt`

## Usage

run `BSPRead.py -h` for help:

```usage: BSPRead.py [-h] [--boosts [BOOSTS]] [--display] filename

View BSP maps

positional arguments:
  filename              BSP map path

optional arguments:
  -h, --help            show this help message and exit
  --boosts [BOOSTS], -b [BOOSTS]
                        find boosts present in map and save edge coordinates
                        to a file (json)
  --display, -d         show map in OpenGL window
  
  example: BSPRead.py maps/de_dust2.bsp -d
```

## Controls
* LMB and drag - rotate camera
* AWSD - move around
* QE - look to left/right
* up/down arrow - move up down
* ctrl+r - reset to origin
* ctrl-g - teleport to location (you need to run the script from some kind of console for that)
