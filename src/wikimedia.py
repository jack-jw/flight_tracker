# wikimedia.py

"""
Get urls from Wikimedia

Functions:
    url()
"""

from requests import get

def url(query):
    """
    Get the full image from Wikimedia

    Takes a query as a string
    Returns a URL to Wikimedia as a string
    """

    response = get("https://commons.wikimedia.org/w/api.php"
                   "?action=query&format=json&list=search&srsearch="
                   + query + "&srnamespace=6&srlimit=1", timeout=60)

    if not response or not response.json()["query"]["search"]:
        return None

    title = response.json()["query"]["search"][0]["title"]
    response = get("https://commons.wikimedia.org/w/api.php"
                   "?action=query&format=json&prop=imageinfo&iiprop=url&titles="
                   + title, timeout=60)
    return list(response.json()["query"]["pages"].values())[0]["imageinfo"][0]["url"]
