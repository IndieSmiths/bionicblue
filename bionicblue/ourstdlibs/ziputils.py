"""Utilities for working with zip files.

Also checks availability of zip storage and compression in zipfile module.

The zipfile usage here was created with help from this tutorial:
https://pymotw.com/3/zipfile/ and, of course, the Python docs.
"""

from tempfile import TemporaryFile



### try importing the zipfile module and check whether it is working fine
### for non-compressed storage


try:

    from zipfile import ZipFile, ZIP_STORED

    with TemporaryFile() as temp:

        with ZipFile(

            temp,
            mode='w',
            compression=ZIP_STORED,

        ) as archive:

            archive.writestr('file.pyl', "{'hello': 'world'}")

except Exception:
    ZIP_STORAGE_AVAILABLE = False

else:
    ZIP_STORAGE_AVAILABLE = True


### create additional utilities/flags depending on whether storage is available
### or not

if ZIP_STORAGE_AVAILABLE:

    ### if storage is available, check whether compression (deflation) is
    ### available too;

    ## try importing the zipfile module and check whether it is working fine
    ## for deflation (compression); although it is usually available, it has
    ## dependencies that the Python docs consider optional, so it seems there's
    ## never 100% certainty that they'll be available;
    ##
    ## in the process create a flag variable to indicate whether compression is
    ## available or not based on the success of the operation

    try:

        from zipfile import ZIP_DEFLATED

        with TemporaryFile() as temp:

            with ZipFile(

                temp,
                mode='w',
                compression=ZIP_DEFLATED,

            ) as archive:

                archive.writestr('file.pyl', "{'hello': 'world'}")

    except Exception:
        ZIP_COMPRESSION_AVAILABLE = False

    else:
        ZIP_COMPRESSION_AVAILABLE = True


    ### create a function to zip an entire folder without compression

    ## main function

    def store_dir_contents_in_zip(dir_path, zip_path):

        with ZipFile(

            str(zip_path),
            mode='w',
            compression=ZIP_STORED,

        ) as archive:

            _store_recursively(archive, dir_path, dir_path)

    ## recursive utility for function above

    def _store_recursively(zip_archive, dir_path, top_path):

        for path in dir_path.iterdir():

            ## if path is a file, copy contents of path within new path inside
            ## archive, named relative to the top path

            if path.is_file():

                zip_archive.write(

                    ## content source
                    str(path),

                    ## relative path within zip archive
                    arcname=str(path.relative_to(top_path))
                )

            ## if path is a dir, pass it to this same function so we can
            ## iterate over its contents recursively copying files as
            ## we find them

            elif path.is_dir():
                _store_recursively(zip_archive, path, top_path)


else:

    ZIP_COMPRESSION_AVAILABLE = False

    def store_dir_contents_in_zip(*args, **kwargs):

        raise RuntimeError(
            "Do not use this function when zip storage is not available"
        )
