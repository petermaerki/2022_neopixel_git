
set -euox pipefail

SYSNAME=rp2

cd /2022_neopixel_git/module_ledstrip/micropython/ports/rp2 && make submodules
cd /2022_neopixel_git/module_ledstrip/micropython/mpy-cross && make
cd /2022_neopixel_git/module_ledstrip/micropython/ports/rp2 && make BOARD=PICO

cd /2022_neopixel_git/module_ledstrip/src
rm -rf build *.mpy
# See: https://github.com/micropython/micropython/issues/6959
# ARCH=armv6m
# -mcpu=cortex-m0 instead of -mcpu=cortex-m3
make ARCH=armv7m
cp /2022_neopixel_git/module_ledstrip/src/ledstrip.mpy /2022_neopixel_git/micropython/ledstrip_${SYSNAME}.mpy
