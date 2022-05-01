set -euox pipefail

SYSNAME=unix

cd /2022_neopixel_git/module_ledstrip/micropython/ports/unix && make submodules
cd /2022_neopixel_git/module_ledstrip/micropython/mpy-cross && make
cd /2022_neopixel_git/module_ledstrip/micropython/ports/unix && make

echo "See: ports/unix/2022_neopixel_git/module_ledstrip/micropython"

# cd /2022_neopixel_git/module_ledstrip/micropython/examples/natmod/features0 && make clean && make
# cp /2022_neopixel_git/module_ledstrip/micropython/examples/natmod/features0/features0.mpy .

cd /2022_neopixel_git/module_ledstrip/src && make clean && make
rm -rf build *.mpy
make ARCH=x64
cp /2022_neopixel_git/module_ledstrip/src/ledstrip.mpy /2022_neopixel_git/micropython/ledstrip_${SYSNAME}.mpy
/2022_neopixel_git/module_ledstrip/micropython/ports/unix/micropython test_ledstrip.py
