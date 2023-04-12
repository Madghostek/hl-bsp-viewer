import numpy as np
import argparse
import json
import os  # for os.path.basename

import utils
from BSP import *
from benchmark import *


def RunWindow(returnedLumps):

    t = TimerMs("RunWindow")
    print(t)

    t.start("imports")
    import pygame
    import pygame.locals
    from camera import Camera
    import opengl_basic
    t.end("imports")

    print("Pygame init")
    t.start("pygame init")
    pygame.init()
    display = (800, 600)
    pygame.display.set_mode(
        display, pygame.locals.DOUBLEBUF | pygame.locals.OPENGL)
    t.end("pygame init")

    t.start("opengl init")
    print("OpenGL init")
    program = opengl_basic.SetupOpenGL(returnedLumps)
    t.end("opengl init")

    # glViewport(0,0,400,400)
    cam = Camera(0, -50, -300, 90, 0, 0)
    pygame.event.set_grab(True)  # lock mouse
    while True:
        keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.event.set_grab(
                        pygame.event.get_grab() ^ 1)  # lock mouse
                if event.key == pygame.K_r and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    cam.reset()

        modifier = 0.2 if pygame.key.get_mods() & pygame.KMOD_SHIFT else 1
        if keys[pygame.K_d]:
            cam.moveLocal(10*modifier, 0)
        if keys[pygame.K_a]:
            cam.moveLocal(-10*modifier, 0)
        if keys[pygame.K_UP]:
            cam.pos[2] -= 10*modifier
        if keys[pygame.K_DOWN]:
            cam.pos[2] += 10*modifier
        if keys[pygame.K_q]:
            cam.angle[2] += 1*modifier
        if keys[pygame.K_e]:
            cam.angle[2] -= 1*modifier
        if keys[pygame.K_w]:
            cam.moveLocal(0, -10*modifier)
        if keys[pygame.K_s]:
            cam.moveLocal(0, 10*modifier)
        if keys[pygame.K_i]:
            cam.pos = np.array([0, 0, 0])
            cam.angle = np.array([0, 0, 0, 0])

        if pygame.key.get_mods() & pygame.KMOD_CTRL and keys[pygame.K_g]:
            tmp = pygame.event.get_grab()
            pygame.event.set_grab(0)
            strXYZ = input("goto (x,y,z):")
            coords = list(map(float, strXYZ.split(",")))
            cam.pos[0] = coords[0]
            cam.pos[1] = coords[1]
            cam.pos[2] = coords[2]
            pygame.event.set_grab(tmp)

        x, y = pygame.mouse.get_rel()
        if pygame.mouse.get_pressed()[0]:
            cam.angle[2] += x*0.1
            cam.angle[0] += y*0.1

        opengl_basic.DrawOpenGL(cam, display, program)

        pygame.display.flip()
        pygame.time.wait(10)

    # cleanup @TODO: Move this to quit event :|
    print("exit")
    opengl_basic.CleanupOpenGL()


def DebugBoost(coords):
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    x, y, z = [], [], []
    for edge in coords:
        print(edge)
        ax.plot([edge[0][0], edge[1][0]], [edge[0][1],
                                           edge[1][1]], [edge[0][2], edge[1][2]])
    plt.show()


def main():

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        prog='BSPViewer.py',
        description='View BSP maps',
        epilog='examples: \n\nShows the map in a window:\n\tpython3 BSPViewer.py maps/de_dust2.bsp -d\n\n\
Saves all trigger_push bounding edges to a json file:\n\tpython3 BSPViewer.py maps/de_dust2.bsp -e trigger_push -o output.json\n\n\
Saves all trigger_teleport bounding edges to a csv file with default name:\n\tpython3 BSPViewer.py maps/de_dust2.bsp -e trigger_teleport -s csv')
    parser.add_argument('filename', type=str, help='BSP map path')
    parser.add_argument('--entities', '-e', nargs='?',
                        help='exports entity bounding lines to display on server.')
    parser.add_argument('--outpath', '-o', nargs='?',
                        help='output path for entities. Supported formats: (json, csv)')
    parser.add_argument('--serialiser', '-s',
                        help='force `outpath` format to something else')
    parser.add_argument('--display', '-d', action='store_true',
                        help='show map in OpenGL window')
    args = parser.parse_args()

    # don't detect serialiser from filename at first
    if args.serialiser not in ('csv', 'json', None):
        print("Serialiser invalid, only csv and json available")
        args.serialiser = None

    # serialiser not specified, but outpath was, try to guess the format
    if not args.serialiser and args.outpath:
        args.serialiser = os.path.splitext(
            args.outpath)[1][1:]  # extension without dot
    else:
        args.serialiser = 'csv'
    base = os.path.splitext(os.path.split(args.filename)[1])[
        0]  # get file name without ext

    # lumps are returned as np.array, sometimes signed.
    # entity lump is special, its just a string
    # lump mask can be used to filter out not needed lumps, this speeds up calculation
    # it's a bitmask, where each lump has nth bit, so use powers of 2
    # if args.display:
    # 	mask|=2**15-1 #everything
    returnedLumps = GetBSPData(args.filename)

    faceIdxs = utils.GetAllModelFaces(1, returnedLumps)

    print(faceIdxs)

    if args.entities:
        ents = utils.EntitiesToPythonDict(
            returnedLumps[LumpsEnum.LUMP_ENTITIES.value])
        # print(ents)

        # list of edges of entities with some desired class
        print(f"finding all {args.entities}...")
        entityLines = utils.GetAllClassLines(
            ents, returnedLumps, args.entities)

        print(args.entities, "count: ", len(entityLines))

        # DebugBoost(list(entityLines.values())[0])

        if args.serialiser == 'json':
            outputString = json.dumps(entityLines)
            fname = base+"_boosts.json" if not args.outpath else args.outpath
            print("writing to ", fname)
            with open(fname, "w") as f:
                f.write(outputString)
        elif args.serialiser == 'csv':
            import csv
            fname = base+"_boosts.csv" if not args.outpath else args.outpath
            print("writing to", fname)
            with open(fname, 'w') as csvfile:
                # writer = csv.writer(csvfile,quoting=csv.QUOTE_NONE, delimiter='\t')
                writer = csv.writer(
                    csvfile, quoting=csv.QUOTE_NONE, delimiter=",")
                for boost in entityLines:
                    for idx, edge in enumerate(entityLines[boost]):
                        values = [
                            base, f"{boost} {idx+1}/{len(entityLines[boost])}", *edge[0], *edge[1], 3]
                        print(values)
                        writer.writerow(values)
        else:
            print("unknown serialiser, use -s, or specify supported extension")

    # debug
    # testverts = np.array([[-100,500,300], [100,500,300], [100,500,500]], dtype=np.float32)
    # testedges = np.array([[0,1],[1,2],[2,0]], dtype=np.int16)
    # testsurfedges = np.array([[0],[1],[2]], dtype=np.int32)
    # testfaces = np.array([[0,3]], dtype=np.int32)

    # returnedLumps[3]=testverts
    # returnedLumps[12]=testedges
    # returnedLumps[13]=testsurfedges
    # returnedLumps[7]=testfaces

    # after parsing
    if args.display:
        RunWindow(returnedLumps)


if __name__ == "__main__":
    main()
