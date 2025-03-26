import polars as pl

def detect_datetime_columns(df: pl.DataFrame) -> list:
    """
    Detects columns in a Polars DataFrame that can be considered as datetime.

    Args:
        df (pl.DataFrame): The input DataFrame.

    Returns:
        list: A list of column names that can be considered as datetime.
    """
    datetime_columns = []

    for column in df.columns:
        # Skip if the column is already a date/datetime
        if df.schema[column] in (pl.Date, pl.Datetime):
            datetime_columns.append(column)
            continue

        # Attempt to parse the column as datetime
        try:
            # Try parsing as datetime with a common format
            parsed = df.with_columns(
                pl.col(column).str.strptime(pl.Datetime, strict=False)
            )
            # If parsing succeeds, add the column to the list
            datetime_columns.append(column)
        except:
            # If parsing fails, skip the column
            continue

    return datetime_columns


import polars as pl
import requests
from io import StringIO
def load_data(url: str) -> pl.DataFrame:

    # Stream the response directly
    response = requests.get("https://api.example.com/large-data", stream=True)

    # Create a file-like object from the stream
    stream = StringIO()
    for chunk in response.iter_content(chunk_size=8192):
        stream.write(chunk.decode('utf-8'))
    stream.seek(0)

    # Read as LazyFrame
    lazy_df = pl.scan_ndjson(stream)