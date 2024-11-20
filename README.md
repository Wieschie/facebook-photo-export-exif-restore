# Facebook Photo Export - add EXIF data

Facebook scrubs all EXIF data from uploaded images.  If you want to export them at any point, they'll be missing the original dates.

This script attempts to parse the exported files to obtain a date and a description, then inserts it into the EXIF data for the relevant image.  This allows any photo management software to sort them by date.

Caveats:

* The dates Facebook provides are the date and time the image was uploaded, not when it was taken.
* Currently, the script only attempts to pull a description if a JSON dump is provided.

Using the JSON export is preferred.

## Usage

```sh
python ./update_exif.py --force-replace <export_directory>
```

`export_directory` is the top level folder of the Facebook export - it should contain a folder called "photos_and_videos".

## Setup

```sh
uv sync
uv run update_exif.py
```
