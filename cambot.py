#!/usr/bin/env python

from fuzzywuzzy import fuzz
import cv2
import re
from optparse import OptionParser
from unidecode import unidecode
import os

parser = OptionParser()
parser.add_option(
    "-p", "--path", dest="path", help="Accepts a single file or directory."
)
parser.add_option("-r", "--rename", dest="rename", action="store_true", default=False)
parser.add_option("-s", "--screenshot", dest="screenshot", action="store_true")
parser.add_option("-v", "--verbose", dest="verbose", action="store_true")
(options, args) = parser.parse_args()

if not options.path:
    print("-p/--path required.")
    parser.print_help()
    exit()

import easyocr

file = options.path


def swap_files(file_path_1, file_path_2):
    print(f"Swapping { file_path_1 } and { file_path_2 }")
    # Ensure both files exist
    if not os.path.exists(file_path_1) or not os.path.exists(file_path_2):
        raise FileNotFoundError("One or both of the file paths provided do not exist.")
    temp_file = file_path_1 + ".temp"
    os.rename(file_path_1, temp_file)
    os.rename(file_path_2, file_path_1)
    os.rename(temp_file, file_path_2)


def parse_title(title):
    pattern = re.compile(r".*s\d+e\d+\s*-\s*([\w\s\'\"\.\&\,]*).{4}")
    return unidecode(re.match(pattern, title).groups()[0])


def get_titles_in_directory(path):
    if os.path.isfile(path):
        directory = os.path.dirname(path)
    else:
        directory = path
    titles = []
    for f in os.listdir(directory):
        title = parse_title(f)
        titles.append(title)
    return titles


# to look for title cards, scan the ~second two minutes, the ~first two minutes
# the ~fifth minute, and then the last two minutes of a video
def get_ranges(vidcap):
    total_frames = int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT))
    segment = int(total_frames / 10)
    return (
        (segment, segment * 2),
        (0, segment),
        (segment * 2, segment * 2.5),
        (total_frames - segment, total_frames),
    )


def scan_video(vidcap, titles, start=0, end=None):
    frame_number = start
    vidcap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    img_batch = []
    while True:
        success, i = vidcap.read()
        if not success:
            break
        # Read text from an image file
        if end and frame_number > end:
            return None
        if frame_number % 48 == 0:
            img_gray = cv2.cvtColor(i, cv2.COLOR_BGR2GRAY)
            # img_gray = i
            results = reader.readtext(
                img_gray, paragraph=True, decoder="greedy", canvas_size=720
            )
            frame_number = frame_number + 48
            vidcap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)

        else:
            frame_number = frame_number + 1
            continue

        for text in results:
            title = [
                title
                for title in titles
                if fuzz.partial_ratio(title.lower(), text[1].lower()) > 90
                and len(text[1]) >= len(title)
            ]
            if len(title) > 0:
                if options.screenshot:
                    cv2.imwrite(f"{ title[0] }{frame_number}.png", i)
                return title[0]


def scan_file(file, titles):
    vidcap = cv2.VideoCapture(file)
    for range in get_ranges(vidcap):
        title = scan_video(vidcap, titles, start=range[0], end=range[1])
        if title and len(title) > 5:
            print(f"File { file } has title { title }")
            return title

titles = get_titles_in_directory(file)
reader = easyocr.Reader(["en"], verbose=False, recog_network="english_g2")

if os.path.isfile(file):
    files = [file]
else:
    if not os.path.isfile(file):
        directory = file
    else:
        directory = os.path.dirname(file)
    files = [directory + "/" + file for file in os.listdir(directory)]


renamed = []
for file in files:
    unscanned = True
    # skip files we already know are correct because they were swapped earlier
    if file in renamed:
        print(f"Already scanned { file }")
        continue
    while unscanned:
        parsed_title = parse_title(file)
        found_title = scan_file(file, titles)
        unscanned = False
        if found_title and parsed_title != found_title:
            print("Found and parsed title do not match.")
            for target_file in files:
                if found_title == parse_title(target_file):
                    if not options.rename:
                        print(f"Would swap { file } and { target_file }")
                    # if we swap two files, scan the file again before moving on
                    # slow and lazy
                    if options.rename:
                        swap_files(file, target_file)
                        renamed.append(target_file)
                        unscanned = True
