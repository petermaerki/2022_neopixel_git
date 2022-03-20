
set -euox pipefail

cd /module_ledstrip/micropython/ports/rp2 && make submodules
cd /module_ledstrip/micropython/mpy-cross && make
cd /module_ledstrip/micropython/ports/rp2 && make BOARD=PICO

cd /module_ledstrip/micropython/module_ledstrip
rm -rf build *.mpy
# See: https://github.com/module_ledstrip/micropython/module_ledstrip/micropython/issues/6959
# ARCH=armv6m
# -mcpu=cortex-m0 instead of -mcpu=cortex-m3
make ARCH=armv6m
