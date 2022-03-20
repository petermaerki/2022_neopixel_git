
set -euox pipefail

cd /module_ledstrip/micropython/ports/stm32 && make submodules
cd /module_ledstrip/micropython/mpy-cross && make
cd /module_ledstrip/micropython/ports/stm32 && make BOARD=PYBV11

echo "See: ports/stm32/build-PYBV11/firmware.dfu"

cd /module_ledstrip/src
rm -rf build *.mpy
make ARCH=armv7m
