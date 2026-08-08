#!/bin/bash
# Run this in a Colab cell with a leading `!` (or `!bash colab_setup.sh`)
# before running the agent. Colab's apt-installed "chromium-browser" is a
# non-functional snap stub on current images, so we install real Google
# Chrome from the official .deb instead.

set -e

pip install -q -r requirements.txt

wget -q -O /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
apt-get install -y -qq /tmp/chrome.deb
google-chrome --version
