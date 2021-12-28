from google.cloud import storage
import re
from os import path, makedirs
import pandas as pd
import glob
import sys

def get_app_name(blob_name):
  return re.match("reviews\/reviews_([a-zA-Z0-9\._]*)_[0-9]{6}.csv", blob_name).group(1)

def select_app(apps):
  if len(apps) == 1:
    name = apps[0]
    print(f"Only one app ({name}) available, using it..")
    return name

  print(f"Detected apps:")
  for i, app in enumerate(apps):
    print(f"{i}: {app}")

  app_index = int(input("Enter the number of the app you want to download: "))
  return apps[app_index]

def list_files(bucket_name):
  print("Connecting to storage bucket..")
  storage_client = storage.Client()
  bucket = storage_client.bucket(bucket_name)

  print(f"Looking for available apps..")
  review_blobs = list(filter(lambda x: x.name.startswith('reviews'), storage_client.list_blobs(bucket)))
  apps = list(set(map(lambda x: get_app_name(x.name), review_blobs)))

  app_name = select_app(apps)
  print(f"Downloading reviews for {app_name}..")
  app_blobs = list(filter(lambda x: x.name.startswith(f'reviews/reviews_{app_name}'), review_blobs))
  if not path.exists("data"):
      makedirs('data')

  for blob in app_blobs:
    _, filename = path.split(blob.name)
    blob.download_to_filename(f"data/{filename}")

  merge_files = [file for file in glob.glob(f'data/reviews_{app_name}_*.csv')]
  combined_csv = pd.concat([pd.read_csv(f, encoding='utf-16') for f in merge_files ])

  # sig helps avoid issues with non-english languages
  output_file = f"data/{app_name}.csv"
  combined_csv.to_csv(output_file, index=False, encoding='utf-16')

  print('Reviews merged into output file: ' + output_file)

if __name__ == '__main__':
  if len(sys.argv) != 2:
    print("Usage: python3 download.py <bucket_name>")
    exit(1)

  bucket_url = sys.argv[1]
  bucket_name = bucket_url.removeprefix("gs://").removesuffix("/").removesuffix("/reviews")
  list_files(bucket_name)