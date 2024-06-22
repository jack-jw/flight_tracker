# jetphotos.py

"""
Get urls for images of aircraft from JetPhotos and optionally cache them

Functions:
    full_url()
    thumb_url()

    full() - caches
    thumb() - caches
"""

from os.path import exists
from requests import get
from bs4 import BeautifulSoup
from paths import LOCAL_IMAGES

def full_url(reg):
    """
    Get the full image of an aircraft
    Includes JetPhotos watermark

    Takes a registration number as a string
    Returns a URL to JetPhotos as a string (or None if not found)
    """

    url = ("https://www.jetphotos.com/showphotos.php?keywords-type=reg&keywords="
           + reg
           + "&search-type=Advanced&keywords-contain=0&sort-order=2")
    response = get(url, timeout=60)
    soup = BeautifulSoup(response.text, "html.parser")
    image_url_element = soup.find("a", class_="result__photoLink")
    if not image_url_element:
        return None

    response = get("https://jetphotos.com" + image_url_element["href"], timeout=60)
    soup = BeautifulSoup(response.text, "html.parser")
    image = soup.find("img", class_="large-photo__img")

    if image:
        return image["srcset"]

    return None

def thumb_url(reg):
    """
    Get a small (thumbnail) image of an aircraft
    Does not include the JetPhotos watermark

    Takes a registration number as a string
    Returns a URL to JetPhotos as a string (or None if not found)
    """

    url = ("https://www.jetphotos.com/showphotos.php?keywords-type=reg&keywords="
           + reg
           + "&search-type=Advanced&keywords-contain=0&sort-order=2")
    response = get(url, timeout=60)
    soup = BeautifulSoup(response.text, "html.parser")
    image = soup.find("img", class_="result__photo")
    if image:
        return "https:" + image["src"]

    return None

def full(reg):
    """
    Get the full image of an aircraft
    Includes JetPhotos watermark
    Caches images locally for faster loading times

    Takes a registration number as a string
    Returns the filename of the image relative to the local images directory
    """

    image = f"{LOCAL_IMAGES}/jp-full-{reg}.jpeg"
    image_filename = f"jp-full-{reg}.jpeg"
    if exists(image):
        return image_filename

    url = full_url(reg)
    if url:
        response = get(url, timeout=60)
        with open(image, "wb") as image_file:
            image_file.write(response.content)
        return image_filename

    return None


def thumb(reg):
    """
    Get a small (thumbnail) image of an aircraft
    Does not include the JetPhotos watermark
    Caches images locally for faster loading times

    Takes a registration number as a string
    Returns the filename of the image relative to the local images directory
    """

    image = f"{LOCAL_IMAGES}/jp-thumb-{reg}.jpeg"
    image_filename = f"jp-thumb-{reg}.jpeg"
    if exists(image):
        return image_filename

    url = thumb_url(reg)
    if url:
        response = get(url, timeout=60)
        with open(image, "wb") as image_file:
            image_file.write(response.content)
        return image_filename

    return None
