"""
Invoke lambda handler locally, and unzip bundle

Example:

$ python run_lambda.py test_configs/digger.json output_dir
"""

import base64
import json
import sys
import tempfile
import zipfile

from handler import generate_terraform


def unzip_buffer_into_directory(buf, output_dir):
    """
    Get buffer with zipped directory
    and unzip it into @output_dir directory
    by doing following:
        * create temporary zip file
        * save buffer into temporary zip file
        * extract temporary zip file into directory
        * remove temporary zip file
    """

    with tempfile.NamedTemporaryFile() as temp_zip_file:
        temp_zip_file.write(buf)
        temp_zip_file.flush()

        with zipfile.ZipFile(temp_zip_file.name) as archive:
            for file in archive.namelist():
                archive.extract(file, output_dir)


if __name__ == "__main__":
    payload = json.load(open(sys.argv[1]))
    output_dir = sys.argv[2]

    resp = generate_terraform(json.load(open(sys.argv[1])), None)
    zipbuf = base64.b64decode(resp["body"])
    unzip_buffer_into_directory(zipbuf, output_dir)

    print(f"Well done! Check {output_dir}/ directory")
