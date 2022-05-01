FROM debian:11.2-slim

RUN apt-get update \
    && apt-get install -y \
    git file python3 python3-pip \
    build-essential libffi-dev git pkg-config \
    gcc-arm-none-eabi binutils-arm-none-eabi

RUN pip3 install --no-cache pyelftools

RUN apt-get install -y cmake

WORKDIR /2022_neopixel_git/module_ledstrip/
