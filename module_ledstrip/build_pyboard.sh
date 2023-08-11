set -euox pipefail

SYSNAME=pyboard

cd /2022_neopixel_git/module_ledstrip/micropython/ports/stm32 && make submodules
cd /2022_neopixel_git/module_ledstrip/micropython/mpy-cross && make
cd /2022_neopixel_git/module_ledstrip/micropython/ports/stm32 && make BOARD=PYBV11

echo "See: ports/stm32/build-PYBV11/firmware.dfu"

cd /2022_neopixel_git/module_ledstrip/src
rm -rf build *.mpy
make ARCH=armv7m
cp /2022_neopixel_git/module_ledstrip/src/ledstrip.mpy /2022_neopixel_git/micropython/ledstrip_${SYSNAME}.mpy
