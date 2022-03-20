# Micropython build in Docker for pyboard, unix and Raspberry Pi PICO

This Docker image will compile your firmware.
This Docker image will compile `module_ledstrip`.

## How to build the firmware


Start container:

```
cd module_ledstrip

git clone --depth 1 --branch v1.18 --single-branch https://github.com/micropython/micropython.git

docker build --tag micropython .

docker run -it --rm --user=`id -u`:`id -g` -v `pwd`:/module_ledstrip --name micropython micropython bash
```

On docker prompt: Build firmware

```
./build_pyboard.sh
./build_unix.sh
./build_rp2.sh
```

## How to build `ledstrip.mpy` for the pyboard

On docker prompt

```
./build_pyboard.sh
```

On host in git-top folder:

```
copy module_ledstrip/str/ledstrip.mpy micropython
```