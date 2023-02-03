# generate an FCEUX movie that plays Irritating Ship
# under construction

import sys

# see https://fceux.com/web/FM2.html
FM2_HEADER = """\
version 3
emuVersion 20500
rerecordCount 0
palFlag 0
romFilename irriship
romChecksum base64:Lr8UgdKKX6oPn0eu4H7Wmg==
guid 00000000-0000-0000-0000-000000000000
fourscore 0
microphone 0
port0 1
port1 0
port2 0
FDS 0
NewPPU 1
RAMInitOption 0
RAMInitSeed 569937536"""

CIRCLE_STEPS = 48  # how many increments in a full turn
(N, NE, E, SE, S, SW, W, NW) = range(0, CIRCLE_STEPS, 6)

# look up coordinates in irriship-map.png
# use e.g. (-2, 20) to turn ship to point left, accelerate for 20 frames,
# turn ship around and decelerate for 20 frames
SCRIPT = (
    (N,  54),
    (NW, 35),
    (E,  46),
    (N,  54),
    (SW, 43),
    (W,  33),
    (N,  30),
    (NE, 40),
    (E,  15),
    (NE, 47),
    (NW, 46),
    (S,  42),
    (W,  40),
)

def fm2_line(buttons=""):
    # format FM2 line (buttons pressed on controller 1)
    # none: "|0|........|||"
    # all:  "|0|RLDUTSBA|||" (T = start)
    buttons2 = "".join((b if b in buttons else ".") for b in "RLDUTSBA")
    return "|0|" + buttons2 + "|||"

def main():
    print(FM2_HEADER)

    # start new game
    for i in range(90):
        print(fm2_line("A"))
    for i in range(10):
        print(fm2_line())

    # ship's current heading in increments of 360/CIRCLE_STEPS degrees,
    # clockwise from north
    shipHeading = 0

    for (heading, frames) in SCRIPT:
        if not -CIRCLE_STEPS // 2 <= heading < CIRCLE_STEPS:
            sys.exit("invalid heading")
        if frames < 1:
            sys.exit("invalid number of frames")

        # -CIRCLE_STEPS // 2 ... CIRCLE_STEPS // 2
        headingDelta = (heading - shipHeading) % CIRCLE_STEPS
        if headingDelta > CIRCLE_STEPS // 2:
            headingDelta -= CIRCLE_STEPS

        # turn
        for i in range(abs(headingDelta)):
            print(fm2_line("L" if headingDelta < 0 else "R"))
        # accelerate
        for i in range(frames):
            print(fm2_line("A"))
        # turn around (clockwise)
        for i in range(CIRCLE_STEPS // 2):
            print(fm2_line("R"))
        # decelerate
        for i in range(frames):
            print(fm2_line("A"))

        shipHeading = (heading + CIRCLE_STEPS // 2) % CIRCLE_STEPS

main()
