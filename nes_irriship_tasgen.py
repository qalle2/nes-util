# generate an FCEUX movie that plays Irritating Ship;
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
(N, NE, E, SE, S, SW, W, NW) = range(0, CIRCLE_STEPS, 6)  # ship's headings

# headings and number of frames to accelerate and decelerate;
# e.g. (NW, 20) = turn ship to northwest, accelerate for 20 frames, turn 180
# degrees and accelerate for 20 frames;
# i.e., after each command, the ship is stationary and faces the opposite
# direction;
# use irriship-map.png as a rough guide;
# this movie only plays the first three checkpoints
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
    (N,  35),
    (NE, 50),
    (W,  47),
    (NE, 43),
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
    currHeading = 0

    for (targetHeading, frames) in SCRIPT:
        if not -CIRCLE_STEPS // 2 <= targetHeading < CIRCLE_STEPS:
            sys.exit("invalid heading")
        if frames < 1:
            sys.exit("invalid number of frames")

        # how much to turn (-CIRCLE_STEPS // 2 ... CIRCLE_STEPS // 2)
        headingDelta = (targetHeading - currHeading) % CIRCLE_STEPS
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

        currHeading = (targetHeading + CIRCLE_STEPS // 2) % CIRCLE_STEPS

main()
