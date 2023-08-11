# Micropython build in Docker for pyboard, unix and Raspberry Pi PICO

This Docker image will compile your firmware.
This Docker image will compile `module_ledstrip`.

## How to build the firmware


Start container:

```
cd 2022_neopixel_git/module_ledstrip

git clone --depth 1 --branch v1.20.0 --single-branch https://github.com/micropython/micropython.git

cd 2022_neopixel_git

docker build --tag micropython module_ledstrip

cd 2022_neopixel_git

docker run -it --rm --user=`id -u`:`id -g` -v `pwd`:/2022_neopixel_git --name micropython micropython bash
```

On docker prompt: Build firmware

```
rm /2022_neopixel_git/micropython/*.mpy

./build_unix.sh

./build_pyboard.sh

./build_rp2.sh
```
