# Regression app for module-level arrays of different sizes (see tests/arrays.py).
# LPython lays out the arrays' memory in an order that is neither source order nor
# name order, so ultra's build has to pair each region with an array of its size.
from lpython import i32
from numpy import empty, int32
from ultra import num

labels: i32[512] = empty(512, dtype=int32)
comps: i32[512] = empty(512, dtype=int32)
icons: i32[512] = empty(512, dtype=int32)
n: i32 = 0
hkind: i32[40] = empty(40, dtype=int32)
hstr: i32[40] = empty(40, dtype=int32)
hwid: i32[40] = empty(40, dtype=int32)
hh: i32[40] = empty(40, dtype=int32)
hkey: i32[40] = empty(40, dtype=int32)
nh: i32 = 0
wlabels: i32[256] = empty(256, dtype=int32)
wprovs: i32[256] = empty(256, dtype=int32)
wicons: i32[256] = empty(256, dtype=int32)
odd: i32[7] = empty(7, dtype=int32)


def update(msg: i32, arg: i32) -> None:
    # Fill every array end to end with a tag of its own.
    i: i32
    for i in range(512):
        labels[i] = 1000 + i
    for i in range(512):
        comps[i] = 2000 + i
    for i in range(512):
        icons[i] = 3000 + i
    for i in range(40):
        hkind[i] = 4000 + i
    for i in range(40):
        hstr[i] = 5000 + i
    for i in range(40):
        hwid[i] = 6000 + i
    for i in range(40):
        hh[i] = 7000 + i
    for i in range(40):
        hkey[i] = 8000 + i
    for i in range(256):
        wlabels[i] = 9000 + i
    for i in range(256):
        wprovs[i] = 10000 + i
    for i in range(256):
        wicons[i] = 11000 + i
    for i in range(7):
        odd[i] = 12000 + i


def view() -> None:
    # Report how many slots lost their tag to an overlapping array.
    bad: i32 = 0
    i: i32
    for i in range(512):
        if labels[i] != 1000 + i:
            bad += 1
    for i in range(512):
        if comps[i] != 2000 + i:
            bad += 1
    for i in range(512):
        if icons[i] != 3000 + i:
            bad += 1
    for i in range(40):
        if hkind[i] != 4000 + i:
            bad += 1
    for i in range(40):
        if hstr[i] != 5000 + i:
            bad += 1
    for i in range(40):
        if hwid[i] != 6000 + i:
            bad += 1
    for i in range(40):
        if hh[i] != 7000 + i:
            bad += 1
    for i in range(40):
        if hkey[i] != 8000 + i:
            bad += 1
    for i in range(256):
        if wlabels[i] != 9000 + i:
            bad += 1
    for i in range(256):
        if wprovs[i] != 10000 + i:
            bad += 1
    for i in range(256):
        if wicons[i] != 11000 + i:
            bad += 1
    for i in range(7):
        if odd[i] != 12000 + i:
            bad += 1
    num(bad)
