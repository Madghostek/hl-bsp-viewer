# hl-bsp-viewer
Python program to parse .bsp files and do stuff with it.

With awful debug shader™ !!!
![awful shader](https://github.com/madghostek/hl-bsp-viewer/blob/main/debugview.png?raw=true)

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
  --display, -d         show map in OpenGL window```
  
  example: BSPRead maps/de_dust2.bsp -d
