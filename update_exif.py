from PIL import Image
import piexif
from bs4 import BeautifulSoup

from datetime import datetime, timezone
from enum import Enum
import json
from pathlib import Path
import os

# relative location of the album folder within the export
ALBUM_PATH: Path = Path("your_facebook_activity/posts/")

# whether to overwrite preexisting EXIF values
force_replace: bool = False


class ExportType(Enum):
    UNKNOWN = 0
    HTML = 1
    JSON = 2


def populate_exif(filename: str, date: datetime, description: str = None):
    """Populate EXIF data in a given image.

    Args:

        filename: image file to copy

        date: datetime to insert into EXIF DateTime and DateTimeOriginal

        description: text to insert into EXIF ImageDescription
    """
    try:
        im = Image.open(filename)
    except IOError:
        print(f"Could not open {filename} - skipping.")
        return

    exif_dict = piexif.load(filename)
    date_str = date.strftime("%Y:%m:%d %H:%M:%S")

    update_exif_value(exif_dict, "Exif", piexif.ExifIFD.DateTimeOriginal, date_str)
    update_exif_value(exif_dict, "0th", piexif.ImageIFD.DateTime, date_str)
    if description is not None:
        update_exif_value(
            exif_dict, "0th", piexif.ImageIFD.ImageDescription, description
        )

    exif_bytes = piexif.dump(exif_dict)
    im.save(filename, exif=exif_bytes)


def update_exif_value(
    exif_dict: dict,
    ifd_name: str,
    tag_type: int,
    new_value: str,
) -> bool:
    """Adds a given value to an exif dictionary.

    Returns:
        True if the value was inserted.  False if the value already existed
        and was not replaced.
    """

    if not force_replace and tag_type in exif_dict[ifd_name]:
        return False
    exif_dict[ifd_name][tag_type] = new_value
    return True


def get_album_files(export_dir: str):
    """ Looks for Facebook export albums in export_dir """
    return (Path(export_dir) / ALBUM_PATH).glob("**/*.html")


def process_html_album(filename: str):
    """Process a single exported album .html file"""
    text = Path(filename).read_text(encoding="utf8")
    soup = BeautifulSoup(text, "html.parser")
    for media in soup.select("._a6_o"):
        media_div = media.findParent('div').parent
        try:
            date_text = media_div.select("div._a72d")[0].text
        except:
            continue
        date = datetime.strptime(date_text, '%b %d, %Y %I:%M:%S %p')
        filename = media.get("src")
        if media.name == 'img':
            populate_exif(filename, date)
        os.utime(filename, (date.timestamp(), date.timestamp()))


def process_json_album(filename: str):
    """Process a single exported album .json file"""
    text = Path(filename).read_text(encoding="utf8")
    parsed_json = json.loads(text)
    for image_data in parsed_json["photos"]:
        filename = image_data["uri"]
        date = datetime.fromtimestamp(int(image_data["creation_timestamp"]), timezone.utc)
        description = None
        if "description" in image_data:
            description = image_data["description"]
        populate_exif(filename, date, description)


def process_all_files(export_dir: str):
    """Finds all albums and processes every image in each album"""

    if not Path(export_dir).exists():
        raise FileNotFoundError(f"{export_dir} not found!")

    os.chdir(export_dir)
    export_type = detect_export_type()
    if export_type is ExportType.UNKNOWN:
        raise Exception("Unrecognized export")

    elif export_type is ExportType.HTML:
        processor = process_html_album

    elif export_type is ExportType.JSON:
        processor = process_json_album

    for file in get_album_files(export_dir):
        print(f"Processing {file}...")
        processor(file)


def detect_export_type() -> ExportType:
    """Detects if an export is HTML or JSON"""
    # album_dir = Path(export_dir) / ALBUM_PATH

    if (ALBUM_PATH / Path("your_photos.html")).exists():
        return ExportType.HTML

    elif (ALBUM_PATH / Path("0.json")).exists():
        return ExportType.JSON

    return ExportType.UNKNOWN


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: ./update_exif.py --force-replace <export_directory>")
        exit()

    if len(sys.argv) == 3:
        if sys.argv[1] == "--force-replace":
            force_replace = True
        else:
            print("Unrecognized option!")
            exit()

    process_all_files(sys.argv[-1])
