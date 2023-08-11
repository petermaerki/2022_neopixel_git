FROM debian:12.1-slim

RUN apt-get update \
    && apt-get install -y \
    git file python3 python3-pip python3-pyelftools\
    build-essential libffi-dev git pkg-config \
    gcc-arm-none-eabi binutils-arm-none-eabi \
    cmake

WORKDIR /2022_neopixel_git/module_ledstrip/
