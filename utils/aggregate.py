import polars as pl
from typing import Dict, List, Union, Any, Optional
import json

# Define available aggregation functions for different data types
NUMERIC_AGGREGATIONS = {
    "mean": lambda col: col.mean(),
    "sum": lambda col: col.sum(),
    "min": lambda col: col.min(),
    "max": lambda col: col.max(),
    "count": lambda col: col.count(),
    "median": lambda col: col.median(),
    "std": lambda col: col.std(),
    "var": lambda col: col.var(),
    "quantile_25": lambda col: col.quantile(0.25),
    "quantile_75": lambda col: col.quantile(0.75),
    "range": lambda col: col.max() - col.min(),
    "iqr": lambda col: col.quantile(0.75) - col.quantile(0.25),
    "null_count": lambda col: col.is_null().sum(),
    "non_null_count": lambda col: col.count()
}

STRING_AGGREGATIONS = {
    "unique_count": lambda col: col.n_unique(),
    "most_frequent": lambda col: col.mode().get(0, None),
    "min_value": lambda col: col.min(),
    "max_value": lambda col: col.max(),
    "mean_length": lambda col: col.str.lengths().mean(),
    "null_count": lambda col: col.is_null().sum(),
    "empty_count": lambda col: (col.str.lengths() == 0).sum(),
    "is_unique": lambda col: col.n_unique() == col.len()
}

DATETIME_AGGREGATIONS = {
    "min_date": lambda col: col.min(),
    "max_date": lambda col: col.max(),
    "count": lambda col: col.count(),
    "unique_days": lambda col: col.dt.day().n_unique(),
    "unique_months": lambda col: col.dt.month().n_unique(),
    "unique_years": lambda col: col.dt.year().n_unique(),
    "most_frequent": lambda col: col.mode().get(0, None),
    "null_count": lambda col: col.is_null().sum(),
    "non_null_count": lambda col: col.count()
}

def get_column_type(df: pl.DataFrame, column: str) -> str:
    """
    Determine the type of a column in a Polars DataFrame.

    Args:
        df (pl.DataFrame): The DataFrame containing the column
        column (str): The name of the column

    Returns:
        str: The type of the column ('numeric', 'string', 'datetime', or 'unknown')
    """
    dtype = df.schema[column]

    if dtype in (pl.Int8, pl.Int16, pl.Int32, pl.Int64,
                pl.UInt8, pl.UInt16, pl.UInt32, pl.UInt64,
                pl.Float32, pl.Float64):
        return 'numeric'
    elif dtype == pl.Utf8:
        return 'string'
    elif dtype in (pl.Date, pl.Datetime, pl.Time):
        return 'datetime'
    else:
        return 'unknown'

def perform_aggregations(df: pl.DataFrame, aggregation_config: Dict[str, List[str]]) -> Dict[str, Dict[str, Any]]:
    """
    Perform multiple aggregations on specified columns of a DataFrame.

    Args:
        df (pl.DataFrame): The DataFrame to aggregate
        aggregation_config (Dict[str, List[str]]): A dictionary mapping column names to lists of aggregation functions
            Example: {'column1': ['mean', 'sum'], 'column2': ['unique_count']}

    Returns:
        Dict[str, Dict[str, Any]]: A dictionary with column names as keys and dictionaries of aggregation results as values
    """
    # Ensure we're working with a DataFrame, not a LazyFrame
    if isinstance(df, pl.LazyFrame):
        df = df.collect()

    results = {}

    for column, aggregations in aggregation_config.items():
        # Skip if column doesn't exist
        if column not in df.columns:
            continue

        column_type = get_column_type(df, column)
        results[column] = {}

        # Apply appropriate aggregations based on column type
        if column_type == 'numeric':
            for agg in aggregations:
                if agg in NUMERIC_AGGREGATIONS:
                    try:
                        result = NUMERIC_AGGREGATIONS[agg](df[column])
                        # Convert to Python native type for JSON serialization
                        if hasattr(result, 'item'):
                            result = result.item()
                        results[column][agg] = result
                    except Exception as e:
                        results[column][agg] = f"Error: {str(e)}"

        elif column_type == 'string':
            for agg in aggregations:
                if agg in STRING_AGGREGATIONS:
                    try:
                        result = STRING_AGGREGATIONS[agg](df[column])
                        # Convert to Python native type for JSON serialization
                        if hasattr(result, 'item'):
                            result = result.item()
                        results[column][agg] = result
                    except Exception as e:
                        results[column][agg] = f"Error: {str(e)}"

        elif column_type == 'datetime':
            for agg in aggregations:
                if agg in DATETIME_AGGREGATIONS:
                    try:
                        result = DATETIME_AGGREGATIONS[agg](df[column])
                        # Convert to Python native type for JSON serialization
                        if hasattr(result, 'item'):
                            result = result.item()
                        # Convert datetime objects to ISO format strings
                        if hasattr(result, 'isoformat'):
                            result = result.isoformat()
                        results[column][agg] = result
                    except Exception as e:
                        results[column][agg] = f"Error: {str(e)}"

    return results

def get_available_aggregations() -> Dict[str, List[str]]:
    """
    Get a dictionary of all available aggregation functions by data type.

    Returns:
        Dict[str, List[str]]: A dictionary mapping data types to lists of available aggregation functions
    """
    return {
        'numeric': list(NUMERIC_AGGREGATIONS.keys()),
        'string': list(STRING_AGGREGATIONS.keys()),
        'datetime': list(DATETIME_AGGREGATIONS.keys())
    }

def get_dataset_column_aggregations(df: pl.DataFrame) -> Dict[str, Dict[str, Any]]:
    """
    Get available aggregation functions for each column in a dataset based on its data type.

    Args:
        df (pl.DataFrame): The DataFrame to analyze

    Returns:
        Dict[str, Dict[str, Any]]: A dictionary with column names as keys and information about each column,
                                  including its data type and available aggregation functions
    """
    # Ensure we're working with a DataFrame, not a LazyFrame
    if isinstance(df, pl.LazyFrame):
        df = df.collect()

    available_aggregations = get_available_aggregations()
    column_info = {}

    for column in df.columns:
        column_type = get_column_type(df, column)

        # Get sample data (first 5 non-null values) for the column
        sample_data = df[column].drop_nulls().head(5).to_list()

        # Convert sample data to serializable format if needed
        serializable_sample = []
        for item in sample_data:
            if hasattr(item, 'isoformat'):  # Handle datetime objects
                serializable_sample.append(item.isoformat())
            else:
                serializable_sample.append(item)

        column_info[column] = {
            'data_type': column_type,
            'polars_type': str(df.schema[column]),
            'sample_data': serializable_sample,
            'available_aggregations': available_aggregations.get(column_type, [])
        }

    return column_info

def extract_dataset_metadata(df: pl.DataFrame) -> Dict[str, Any]:
    """
    Extract metadata from a dataset including column information and possible aggregations.

    Args:
        df (pl.DataFrame): The DataFrame to analyze

    Returns:
        Dict[str, Any]: A dictionary containing dataset metadata
    """
    # Ensure we're working with a DataFrame, not a LazyFrame
    if isinstance(df, pl.LazyFrame):
        df = df.collect()

    # Get basic dataset info
    num_rows = df.height
    num_columns = len(df.columns)

    # Get column metadata and possible aggregations
    columns_metadata = get_dataset_column_aggregations(df)

    # Calculate additional dataset statistics
    null_counts = {col: df[col].null_count() for col in df.columns}
    total_null_count = sum(null_counts.values())

    # Create metadata dictionary
    metadata = {
        "dataset_info": {
            "num_rows": num_rows,
            "num_columns": num_columns,
            "total_null_count": total_null_count,
            "memory_usage": df.estimated_size(),
        },
        "columns": columns_metadata,
        "null_counts": null_counts
    }

    return metadata


# For large datasets, consider using Polars' lazy API (pl.LazyFrame) to optimize performance.

            # import polars as pl
            # from datetime import datetime

            # # Create a large dataset with a datetime column
            # data = {
            #     "date": [datetime(2023, 1, 1), datetime(2023, 1, 2), datetime(2023, 1, 3)] * 1_000_000,
            #     "values": [1, 2, 3] * 1_000_000
            # }

            # # Convert to a LazyFrame
            # lf = pl.LazyFrame(data)

            # # Define the aggregations
            # aggregations = [
            #     pl.col("values").mean().alias("mean_value"),
            #     pl.col("values").sum().alias("sum_value"),
            #     pl.col("date").min().alias("min_date"),
            #     pl.col("date").max().alias("max_date")
            # ]

            # # Perform the aggregations
            # result = (
            #     lf.group_by(pl.col("date").dt.year().alias("year"))  # Group by year
            #     .agg(aggregations)                                   # Apply the aggregations
            #     .collect()                                           # Execute the query
            # )

            # # Print the result
            # print(result)