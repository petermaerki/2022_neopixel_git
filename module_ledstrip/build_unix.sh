
set -euox pipefail

cd /module_ledstrip/micropython/ports/unix && make submodules
cd /module_ledstrip/micropython/mpy-cross && make
cd /module_ledstrip/micropython/ports/unix && make

echo "See: ports/unix/module_ledstrip/micropython"

# cd /module_ledstrip/micropython/examples/natmod/features0 && make clean && make
# cp /module_ledstrip/micropython/examples/natmod/features0/features0.mpy .

cd /module_ledstrip/src && make clean && make
rm -rf build *.mpy
make
/module_ledstrip/micropython/ports/unix/micropython test_ledstrip.py
