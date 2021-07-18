from PIL import Image
import requests
import os
from screeninfo import get_monitors
import random
import subprocess

# imports for background
import cv2
import numpy as np
from skimage import io

def get_screen_resolution():
    for m in get_monitors():
        width = m.width
        height = m.height
    return (width, height)

def set_envir():
    pid = subprocess.check_output(["pgrep", "gnome-session"]).decode("utf-8").strip()
    pid = pid.split('\n')[0]
    cmd = "grep -z DBUS_SESSION_BUS_ADDRESS /proc/"+str(pid)+"/environ|cut -d= -f2-"
    os.environ["DBUS_SESSION_BUS_ADDRESS"] = subprocess.check_output(
        ['/bin/bash', '-c', cmd]).decode("utf-8").strip().replace("\0", "")

def get_background_colour(image, save_comic_path):
    '''
    Determines dominant colour in image to be used as border colour. Adapted from https://stackoverflow.com/a/43111221
    '''
    image = io.imread(save_comic_path)[:, :, :-1]
    pixels = np.float32(image.reshape(-1, 3))
    n_colors = 3
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 200, .1)
    flags = cv2.KMEANS_RANDOM_CENTERS

    _, labels, palette = cv2.kmeans(pixels, n_colors, None, criteria, 10, flags)
    _, counts = np.unique(labels, return_counts=True)
    dominant = palette[np.argmax(counts)]

    return tuple(dominant)

def resize_image(comic, screen_size, url):
    '''
    Resizes image to fit desktop
    '''
    old_comic_width = comic.size[0]
    old_comic_height = comic.size[1]
    scaling_factor = 1.4
    if old_comic_width >= screen_size[0]:
        scaling_factor = 0.8 * screen_size[0] / old_comic_width
    if old_comic_height >= screen_size[1]:
        scaling_factor = 0.5 * screen_size[0] / old_comic_height
    new_comic_width = int(old_comic_width * scaling_factor)
    new_comic_height = int(old_comic_height * scaling_factor)

    new_comic_size = (new_comic_width, new_comic_height)
    comic = comic.resize(new_comic_size, Image.ANTIALIAS)

    wallpaper_size = screen_size
    background_colour = get_background_colour(comic, url)
    wallpaper = Image.new("RGB", wallpaper_size, color = background_colour)
    wallpaper.paste(comic, ((wallpaper_size[0]-new_comic_size[0])//2,(wallpaper_size[1]-new_comic_size[1])//2), mask=comic)

    return wallpaper

def pick_comic(current_dir):
    # TODO: fetch number of latest comic to update utils

    # Open list of comics that have not been shown in this cycle
    path_in = os.path.join(current_dir + '/utils', 'eligible_comics.txt')
    with open(path_in) as utils_file:
        comics_not_shown = utils_file.read().splitlines()
        if comics_not_shown == []:
            comics_not_shown = list(range(0, 400))

    # get random comic that has not been shown yet
    url = None
    while url == None:
        comic_candidate = str(random.randint(0, 400))
        if comic_candidate in comics_not_shown:
            url = f"https://falseknees.com/imgs/{comic_candidate}.png"

            # Remove comic from eligible comics
            comics_not_shown.remove(comic_candidate)
            utils_file = open(path_in, "w")
            for comic in comics_not_shown:
                utils_file.write(str(comic) + "\n")
            utils_file.close()

    return url

def main():
    current_dir = os.path.dirname('/home/wessel/desktop-randomizer/')
    comics_path = current_dir + '/comics'
    wallpapers_path = current_dir + '/wallpapers'
    # Get screen resolution
    screen_size = get_screen_resolution()

    # Download and open image
    url = pick_comic(current_dir)
    filename = url.split('/')[-1]
    image = Image.open(requests.get(url, stream=True).raw)

    # Save comic
    save_comic_path = comics_path + '/' + filename
    image.save(save_comic_path, 'png', quality=100)

    # Process image
    image = resize_image(image, screen_size, save_comic_path)

    # # Save desktop image
    save_wallpaper_path = wallpapers_path + '/' + filename
    image.save(save_wallpaper_path, 'png', quality=100)

    # Set desktop image
    set_envir()
    os.system(f"gsettings set org.gnome.desktop.background picture-uri {save_wallpaper_path}")


if __name__ == "__main__":
	main()
