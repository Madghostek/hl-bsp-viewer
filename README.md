# hl-bsp-viewer
Python program to parse .bsp files and do stuff with it.

With awful debug shader™ !!!
![awful shader](https://github.com/madghostek/hl-bsp-viewer/blob/main/debugview.png?raw=true)

## Requirements
use `pip unfreeze requirements.txt`

## Usage

run `BSPViewer.py -h` for help:

```usage: BSPViewer.py [-h] [--boosts [BOOSTS]] [--serialiser SERIALISER] [--display] filename

View BSP maps

positional arguments:
  filename              BSP map path

optional arguments:
  -h, --help            show this help message and exit
  --boosts [BOOSTS], -b [BOOSTS]
                        find boosts present in map and save edge coordinates to a file. If `--serialiser` not specified,
                        deduces output format from extension (json or csv)
  --serialiser SERIALISER, -s SERIALISER
                        `boosts` optput format, if no output filename given
  --display, -d         show map in OpenGL window

examples: 	python3 BSPViewer.py maps/de_dust2.bsp -d
		python3 BSPViewer.py maps/de_dust2.bsp -b output.json
		python3 BSPViewer.py maps/de_dust2.bsp -b -s csv
```

## Controls
* LMB and drag - rotate camera
* AWSD - move around
* QE - look to left/right
* up/down arrow - move up down
* ctrl+r - reset to origin
* ctrl-g - teleport to location (you need to run the script from some kind of console for that)
