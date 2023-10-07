#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import re
import click
import socket
import sys
import requests
import json
from requests import ConnectionError
from lxml import html


def internet_connection(server: str = "www.google.com", port: int = 80):
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  sock.settimeout(5)
  try:
    sock.connect((server, port))
    return True
  except socket.error:
    return False
  finally:
    sock.close()

def validate_movie(url: str):
  imdb_url_regex="^(https?://)?(www\.)?imdb\.com/title/tt\d{6,}(/(\?.*)?)?$"
  if re.match('^\d{6,}$', url):
    url = f"https://www.imdb.com/title/tt{url}"
  elif re.match('^tt\d{6,}$', url):
    url = f"https://www.imdb.com/title/{url}"
  elif not re.match(imdb_url_regex, url):
    click.echo(f'\x1b[31;1mInvalid movie: "{url}". Must match regex "{imdb_url_regex}"\x1b[0m')
    sys.exit(1)
  return url

def _real_main(url: str, UserAgent = None):
  data = {}
  request = requests.get(
    url,
    headers={
      "User-Agent": "" if UserAgent is None else UserAgent
    })
  if 400<=request.status_code<=499:
    raise ValueError(f"{url} is invalid. Got HTTP {request.status_code} {request.reason}.")
  tree = html.fromstring(request.text)
  main_data = json.loads([td.text for td in tree.xpath("//script[@id=\"__NEXT_DATA__\"][@type=\"application/json\"]")][0])
  page_data = json.loads([td.text for td in tree.xpath("//script[@type=\"application/ld+json\"]")][0])

  data['raw']={"main": main_data, "page": page_data}
  data['release_date'] = {
    "year": main_data['props']['pageProps']['aboveTheFoldData']['releaseDate']['year'],
    "month": main_data['props']['pageProps']['aboveTheFoldData']['releaseDate']['month'],
    "day": main_data['props']['pageProps']['aboveTheFoldData']['releaseDate']['day']
  }
  data['reviews'] = {
    "value": main_data['props']['pageProps']['aboveTheFoldData']['ratingsSummary']['aggregateRating'],
    "reviews": main_data['props']['pageProps']['aboveTheFoldData']['ratingsSummary']['voteCount']
  }
  data['thumbnail'] = {
    "id": main_data['props']['pageProps']['aboveTheFoldData']['primaryImage']['id'],
    "width": main_data['props']['pageProps']['aboveTheFoldData']['primaryImage']['width'],
    "height": main_data['props']['pageProps']['aboveTheFoldData']['primaryImage']['height'],
    "image": main_data['props']['pageProps']['aboveTheFoldData']['primaryImage']['url'],
    "caption": main_data['props']['pageProps']['aboveTheFoldData']['primaryImage']['caption']['plainText']
  }
  data['primary_video'] = [
    {
      "resolution": i['displayName']['value'],
      "language": i['displayName']['language'],
      "mime": i['mimeType'],
      "video": i['url']
    } for i in main_data['props']['pageProps']['aboveTheFoldData']['primaryVideos']['edges'][0]['node']['playbackURLs']
  ]
  return json.dumps(data)


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.argument("movie", type=str)
def main(movie: str):
  """
  Get information on over 1,000,000+ movies right from the terminal.
  """
  
  movie = validate_movie(movie)

  # Check if the user is connected to the internet
  if not internet_connection():
    click.echo("Please connect to the internet to use the IMDB-Scrapper.")
    raise
  
  print(_real_main(movie))



if __name__ == "__main__":
  sys.exit(main())