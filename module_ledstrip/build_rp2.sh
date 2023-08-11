
set -euox pipefail

SYSNAME=rp2

cd /2022_neopixel_git/module_ledstrip/micropython/ports/rp2 && make submodules
cd /2022_neopixel_git/module_ledstrip/micropython/mpy-cross && make
cd /2022_neopixel_git/module_ledstrip/micropython/ports/rp2 && make BOARD=PICO

cd /2022_neopixel_git/module_ledstrip/src
rm -rf build *.mpy
make ARCH=armv6m
cp /2022_neopixel_git/module_ledstrip/src/ledstrip.mpy /2022_neopixel_git/micropython/ledstrip_${SYSNAME}.mpy
