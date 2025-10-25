"""
Download youtube shorts using invidious api
"""

import requests
import json
import os
from concurrent.futures import ThreadPoolExecutor
import itertools


instance = "inv.perditum.com"


def get_search_results(search: str, num: int):
    """ Return a list of video ids from the search result """
    p = {
        "q": search,
        "page": 1,
        "sort": "relevance",
        "date": "year",
        "duration": "short",
        "type": "video",
    }

    response = requests.get(f"https://{instance}/api/v1/search/", params=p)
    x = json.loads(response.text)

    num_fetched = len(x)
    print(f"Fetched {num_fetched} videos")

    result = [x[i]["videoId"] for i in range(min(num, num_fetched))]

    return result


def save_thumbnail(id: str, dir: str):
    """ Save the thumbnail from the given video id to a file """

    response = requests.get(f"https://{instance}/api/v1/videos/{id}")
    x = json.loads(response.text)


video_dir = "videos/"


def save_video(id: str, dir: str):
    """ Save the video from the given the video id to a file """

    response = requests.get(f"https://{instance}/api/v1/videos/{id}")
    x = json.loads(response.text)

    url = x["formatStreams"][-1]["url"]
    title = x["title"]

    data = requests.get(url).content

    # folder = os.path(dir)
    name = title + ".mp4"
    path = os.path.join(dir, name)

    if not os.path.exists(dir):
        print(f"{dir} does not exist.")
        return

    with open(path, "wb") as writer:
        writer.write(data)


def download_func(n, id, video_dir):
    print(f"Downloading video {n + 1}...")
    save_video(id, video_dir)
    print(f"Finished downloading video {n + 1}.")


def main():
    """ Main function """

    search = input("Enter your search: ")
    num_videos = int(input("Enter number of videos: "))

    print(f"Getting the first {num_videos} search results...")
    ids = get_search_results(search, num_videos)

    if not os.path.exists(video_dir):
        print(f"{video_dir} does not exist. Creating {video_dir}")
        os.mkdir(video_dir)

    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(download_func, range(len(ids)), ids, itertools.repeat(video_dir))

    print("Finished downloading!")


if __name__ == "__main__":
    main()
