# cambot

[cambot](https://mst3k.fandom.com/wiki/Cambot) is more of a silly experiment than a full-fledged tool. You probably shouldn't use it without reading the code. And then you might ask an LLM to write you a better one. I have a bunch of old recorded TV shows added to a Jellyfin server. They are all named in the old XBMC style like:

```
s01e01 - Episode One.mkv
s01e02 - Episode Two.mkv
s01e03 - Episode Three.mkv
s01e04 - Episode Four.mkv
```

While they are all named correctly, several times they were out of order. I would scan through them with my eyeballs, looking for title cards, and swapping them around.

This script just does that. It works surprisingly well, but isn't perfect. It will get confused if the title of an episode happens to just appear in a scene for example, but usually it works fine.

cambot doesn't make any sophisticated attempts to identify content, but it will "watch" shows named that way, and compare their titles to what should be in the directory. It scans the directory and says "This directory has Episode One, Episode Two, Episode three and Episode Four in it" it then "watches" each one using opencv2 and easyocr to identify title cards containing those names. It does not watch the whole video in sequence. Instead it scans around in segments, hitting 10-20%, then 0-10%, then 20-25% of the videos, then 90-100% of the videos total length. Titles are pretty much never in the middle, and the OCR is pretty slow. If some are out of order, it can swap them. That's it. It works and is reasonably fast on my 7900 XTX.

# Usage

If the files above have episodes two and four swapped, and have recognizable title cards, cambot would produce output like this:

```
$ cambot.py --path /path/to/videos/
/path/to/videos/s01e01 - Episode One.mkv has tile Episode One
/path/to/videos/s01e02 - Episode Two.mkv has tile Episode Four
/path/to/videos/s01e03 - Episode Three.mkv has tile Episode Three
/path/to/videos/s01e04 - Episode Four.mkv has tile Episode Two
```

It accepts two options in addition to --path. -s/--screenshot will save a screenshot of the captured title card, and -r/--rename will rename the files it finds with incorrect names.

# Dockerfile

I included the Dockerfile I use to run this. It only works using ROCm as I only have an AMD GPU around, but could be easily adapted if you have something else and the same problem.

I build it like this:

```
$ podman build . -t cambot
```

And then get a shell like this:

```
$ podman run --rm -it --network=host --device=/dev/kfd --device=/dev/dri \
--ipc=host --group-add video --cap-add=SYS_PTRACE --volume /path/to/cambot:/code \
--volume /video/:/path/to/video\
--security-opt seccomp=unconfined opencv /bin/bash
```
