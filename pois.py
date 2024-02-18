import json
import tempfile
import zipfile
import dlt
from dlt.sources.helpers import requests


@dlt.source(max_table_nesting=0)
def pois_source(api_secret_key=dlt.secrets.value, api_url=dlt.secrets.value):

    return pois_resource(api_secret_key, api_url)


def _create_url(api_secret_key, api_url):
    """Constructs the url"""
    return f"{api_url}{api_secret_key}"


@dlt.resource(write_disposition="append")
def pois_resource(api_secret_key=dlt.secrets.value, api_url=dlt.secrets.value):
    url = _create_url(api_secret_key, api_url)

    # check if url looks fine
    print(url)

    with requests.get(url, stream=True) as response:
        response.raise_for_status()  # Raise an exception for bad responses (e.g., 404)

        # Create a temporary file to hold the zip file content
        with tempfile.TemporaryFile() as tmp_file:
            for chunk in response.iter_content(
                chunk_size=8192
            ):  # Adjust chunk size as needed
                if chunk:
                    tmp_file.write(chunk)

            # Seek to the beginning of the file
            tmp_file.seek(0)
            # delete this line
            tmp_file = "/home/matzi/Downloads/flux-18731-202402112311.zip"
            # Open the zip file
            with zipfile.ZipFile(tmp_file, "r") as zip_ref:
                # Get all file paths in the zip file
                all_files = zip_ref.filelist

                # Filter files matching the specified path structure
                json_files = [
                    f
                    for f in all_files
                    if f.filename.startswith("objects/")
                    and f.filename.endswith(".json")
                ]

                # Yield JSON content from filtered files
                for filename in json_files:
                    with zip_ref.open(filename) as json_file:
                        json_content = json_file.read().decode("utf-8")

                        # Parse JSON content
                        json_object = json.loads(json_content)
                        yield json_object


if __name__ == "__main__":
    # configure the pipeline with your destination details
    pipeline = dlt.pipeline(
        import_schema_path="schemas/import",
        export_schema_path="schemas/export",
        pipeline_name="pois",
        destination="snowflake",
        dataset_name="raw_pois_data",
        progress=dlt.progress.tqdm(colour="yellow"),
    )

    # run the pipeline with your parameters
    info = pipeline.run(pois_source())
    print(info)
