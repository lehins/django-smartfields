#!/bin/bash

sudo apt-get update
sudo apt-get -y install autoconf automake build-essential libass-dev libfreetype6-dev libgpac-dev \
  libtheora-dev libtool libvorbis-dev pkg-config texi2html zlib1g-dev unzip
mkdir ~/ffmpeg_sources
cd ~/ffmpeg_sources

# yasm 1.2.0

sudo apt-get install yasm

# libx264

cd ~/ffmpeg_sources
wget http://download.videolan.org/pub/x264/snapshots/last_x264.tar.bz2
tar xjvf last_x264.tar.bz2
cd x264-snapshot*
./configure --prefix="$HOME/ffmpeg_build" --bindir="$HOME/bin" --enable-static
make
make install
make distclean

# libfdk-aac

cd ~/ffmpeg_sources
wget -O fdk-aac.zip https://github.com/mstorsjo/fdk-aac/zipball/master
unzip fdk-aac.zip
cd mstorsjo-fdk-aac*
autoreconf -fiv
./configure --prefix="$HOME/ffmpeg_build" --disable-shared
make
make install
make distclean

# libvpx

cd ~/ffmpeg_sources
wget http://webm.googlecode.com/files/libvpx-v1.3.0.tar.bz2
tar xjvf libvpx-v1.3.0.tar.bz2
cd libvpx-v1.3.0
./configure --prefix="$HOME/ffmpeg_build" --disable-examples
make
make install
make clean

# libmp3lame 3.99.5
sudo apt-get install libmp3lame-dev

# liboupus 1.1
sudo apt-get install libopus-dev

# ffmpeg

cd ~/ffmpeg_sources
wget http://ffmpeg.org/releases/ffmpeg-snapshot.tar.bz2
tar xjvf ffmpeg-snapshot.tar.bz2
cd ffmpeg
PKG_CONFIG_PATH="$HOME/ffmpeg_build/lib/pkgconfig"
export PKG_CONFIG_PATH
./configure --prefix="$HOME/ffmpeg_build" --extra-cflags="-I$HOME/ffmpeg_build/include" \
   --extra-ldflags="-L$HOME/ffmpeg_build/lib" --bindir="$HOME/bin" --extra-libs="-ldl" --enable-gpl \
   --enable-libass --enable-libfdk-aac --enable-libfreetype --enable-libmp3lame --enable-libopus \
   --enable-libtheora --enable-libvorbis --enable-libvpx --enable-libx264 --enable-nonfree
make
make install
make distclean
hash -r

# put stuff in right place:

sudo mkdir -p /opt/ffmpeg
sudo cp ~/bin/* /opt/ffmpeg/
sudo ln -s /opt/ffmpeg/ffmpeg /usr/local/bin/ffmpeg
sudo ln -s /opt/ffmpeg/ffplay /usr/local/bin/ffplay
sudo ln -s /opt/ffmpeg/ffprobe /usr/local/bin/ffprobe
sudo ln -s /opt/ffmpeg/ffserver /usr/local/bin/ffserver
sudo ln -s /opt/ffmpeg/vsyasm /usr/local/bin/vsyasm
sudo ln -s /opt/ffmpeg/x264 /usr/local/bin/x264
sudo ln -s /opt/ffmpeg/yasm /usr/local/bin/yasm
sudo ln -s /opt/ffmpeg/ytasm /usr/local/bin/ytasm
