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
    # Basic datetime aggregations
    "min_date": lambda col: col.min(),
    "max_date": lambda col: col.max(),
    "count": lambda col: col.count(),
    "unique_days": lambda col: col.dt.day().n_unique(),
    "unique_months": lambda col: col.dt.month().n_unique(),
    "unique_years": lambda col: col.dt.year().n_unique(),
    "most_frequent": lambda col: col.mode().get(0, None),
    "null_count": lambda col: col.is_null().sum(),
    "non_null_count": lambda col: col.count(),

    # Time-based aggregations
    "daily": lambda col: "daily_aggregation",  # This is a placeholder, actual implementation in perform_aggregations
    "monthly": lambda col: "monthly_aggregation",  # This is a placeholder, actual implementation in perform_aggregations
    "quarterly": lambda col: "quarterly_aggregation",  # This is a placeholder, actual implementation in perform_aggregations
    "yearly": lambda col: "yearly_aggregation"  # This is a placeholder, actual implementation in perform_aggregations
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
                        # Handle special time-based aggregations
                        if agg in ['daily', 'monthly', 'quarterly', 'yearly']:
                            # Perform time-based aggregation
                            time_agg_result = perform_time_based_aggregation(df, column, agg)
                            results[column][agg] = time_agg_result
                        else:
                            # Handle regular datetime aggregations
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

def perform_time_based_aggregation(df: Union[pl.DataFrame, pl.LazyFrame], date_column: str, aggregation_type: str,
                                max_periods: int = 1000) -> Dict[str, Any]:
    """
    Perform time-based aggregation on a date column.
    Optimized for large datasets using lazy evaluation.

    Args:
        df (Union[pl.DataFrame, pl.LazyFrame]): The DataFrame or LazyFrame to aggregate
        date_column (str): The name of the date column
        aggregation_type (str): The type of time-based aggregation ('daily', 'monthly', 'quarterly', 'yearly')
        max_periods (int, optional): Maximum number of time periods to return

    Returns:
        Dict[str, Any]: A dictionary with time periods as keys and counts as values
    """
    try:
        # Convert to LazyFrame for optimized processing
        if isinstance(df, pl.DataFrame):
            lf = df.lazy()
        else:
            lf = df  # Already a LazyFrame

        # Get schema information without collecting
        schema = lf.schema

        # Make sure we're working with a datetime column
        column_type = get_column_type_from_schema(schema, date_column)
        if column_type != 'datetime':
            return {"error": f"Column {date_column} is not a datetime column (type: {column_type})"}

        # Create the appropriate time period expression based on aggregation type
        time_period_expr = create_time_period_expression(date_column, aggregation_type)

        # Set the period format for the response
        if aggregation_type == 'daily':
            period_format = "Daily"
        elif aggregation_type == 'monthly':
            period_format = "Monthly"
        elif aggregation_type == 'quarterly':
            period_format = "Quarterly"
        elif aggregation_type == 'yearly':
            period_format = "Yearly"
        else:
            return {"error": f"Unsupported aggregation type: {aggregation_type}"}

        # Create a query that adds the time period column, groups by it, and counts
        agg_query = (
            lf.with_columns(time_period_expr)
            .group_by('time_period')
            .agg(pl.count().alias('count'))
            .sort('time_period')
        )

        # Execute the query
        agg_result = agg_query.collect()

        # Check if we have too many time periods
        if agg_result.height > max_periods:
            print(f"Warning: Time-based aggregation has {agg_result.height} periods, limiting to {max_periods}")
            # For now, just take the first max_periods
            agg_result = agg_result.head(max_periods)

        # Convert to lists for the response
        time_periods = agg_result['time_period'].to_list()
        counts = agg_result['count'].to_list()

        # Create a structured response
        result = {
            "type": period_format,
            "data": dict(zip(time_periods, counts)),
            "periods": time_periods,
            "counts": counts,
            "total_periods": len(time_periods),
            "limited": agg_result.height >= max_periods
        }

        return result
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return {
            "error": f"Error performing {aggregation_type} aggregation: {str(e)}",
            "details": error_details
        }

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

def get_dataset_column_aggregations(df: Union[pl.DataFrame, pl.LazyFrame],
                                sample_rows: int = 5) -> Dict[str, Dict[str, Any]]:
    """
    Get available aggregation functions for each column in a dataset based on its data type.
    Optimized for large datasets using lazy evaluation.

    Args:
        df (Union[pl.DataFrame, pl.LazyFrame]): The DataFrame or LazyFrame to analyze
        sample_rows (int, optional): Number of sample rows to include for each column

    Returns:
        Dict[str, Dict[str, Any]]: A dictionary with column names as keys and information about each column,
                                  including its data type and available aggregation functions
    """
    # Convert to LazyFrame for optimized processing
    if isinstance(df, pl.DataFrame):
        lf = df.lazy()
    else:
        lf = df  # Already a LazyFrame

    # Get schema information without collecting
    schema = lf.schema

    # Get available aggregations
    available_aggregations = get_available_aggregations()

    # Initialize column info dictionary
    column_info = {}

    # Get sample data for all columns in a single query
    # This is more efficient than querying each column separately
    sample_df = lf.filter(~pl.all_horizontal(pl.all().is_null())).head(sample_rows).collect()

    # Process each column
    for column, dtype in schema.items():
        # Determine column type from schema
        column_type = get_column_type_from_schema(schema, column)

        # Get sample data for the column
        if column in sample_df.columns:
            sample_data = sample_df[column].to_list()

            # Convert sample data to serializable format if needed
            serializable_sample = []
            for item in sample_data:
                if item is None:
                    serializable_sample.append(None)
                elif hasattr(item, 'isoformat'):  # Handle datetime objects
                    serializable_sample.append(item.isoformat())
                else:
                    serializable_sample.append(item)
        else:
            serializable_sample = []

        # Get basic statistics for the column
        try:
            # For numeric columns, get min, max, mean
            if column_type == 'numeric':
                stats_query = lf.select([
                    pl.col(column).min().alias('min'),
                    pl.col(column).max().alias('max'),
                    pl.col(column).mean().alias('mean'),
                    pl.col(column).null_count().alias('null_count')
                ])
                stats = stats_query.collect().to_dicts()[0]
            # For datetime columns, get min, max dates
            elif column_type == 'datetime':
                stats_query = lf.select([
                    pl.col(column).min().alias('min'),
                    pl.col(column).max().alias('max'),
                    pl.col(column).null_count().alias('null_count')
                ])
                stats = stats_query.collect().to_dicts()[0]
                # Convert datetime objects to ISO format strings
                if stats['min'] and hasattr(stats['min'], 'isoformat'):
                    stats['min'] = stats['min'].isoformat()
                if stats['max'] and hasattr(stats['max'], 'isoformat'):
                    stats['max'] = stats['max'].isoformat()
            # For string columns, get unique count
            elif column_type == 'string':
                stats_query = lf.select([
                    pl.col(column).n_unique().alias('unique_count'),
                    pl.col(column).null_count().alias('null_count')
                ])
                stats = stats_query.collect().to_dicts()[0]
            else:
                stats = {'null_count': lf.select(pl.col(column).null_count()).collect().item()}
        except Exception as e:
            stats = {'error': str(e)}

        # Create column info
        column_info[column] = {
            'data_type': column_type,
            'polars_type': str(dtype),
            'sample_data': serializable_sample,
            'available_aggregations': available_aggregations.get(column_type, []),
            'statistics': stats
        }

    return column_info

def detect_date_columns(df: Union[pl.DataFrame, pl.LazyFrame],
                     sample_size: int = 100,
                     threshold: float = 0.8) -> Dict[str, str]:
    """
    Detect string columns that might contain dates and return their inferred data types.
    Optimized for large datasets using lazy evaluation.

    Args:
        df (Union[pl.DataFrame, pl.LazyFrame]): The DataFrame or LazyFrame to analyze
        sample_size (int, optional): Number of sample rows to check for date patterns
        threshold (float, optional): Threshold for classifying a column as a date column (0.0-1.0)

    Returns:
        Dict[str, str]: A dictionary mapping column names to their inferred data types
    """
    import re

    # Convert to LazyFrame for optimized processing
    if isinstance(df, pl.DataFrame):
        lf = df.lazy()
    else:
        lf = df  # Already a LazyFrame

    # Get schema information without collecting
    schema = lf.schema

    # Common date patterns to check
    date_patterns = [
        # ISO format: YYYY-MM-DD
        r'^\d{4}-\d{2}-\d{2}$',
        # US format: MM/DD/YYYY
        r'^\d{1,2}/\d{1,2}/\d{4}$',
        # European format: DD/MM/YYYY
        r'^\d{1,2}\.\d{1,2}\.\d{4}$',
        r'^\d{1,2}-\d{1,2}-\d{4}$',
        # With time component
        r'^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}',
        r'^\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}'
    ]

    # Compile patterns for efficiency
    compiled_patterns = [re.compile(pattern) for pattern in date_patterns]

    # Function to check if a string matches any date pattern
    def is_date_string(s):
        if not isinstance(s, str):
            return False
        return any(pattern.match(s) for pattern in compiled_patterns)

    inferred_types = {}

    # Get all string columns
    string_columns = [col for col, dtype in schema.items() if dtype == pl.Utf8]

    if not string_columns:
        return inferred_types

    # Get a sample of data for all string columns at once
    sample_df = (
        lf.select(string_columns)
        .filter(~pl.all_horizontal(pl.all().is_null()))
        .head(sample_size)
        .collect()
    )

    # Check each string column
    for col_name in string_columns:
        # Skip if column not in sample (should not happen, but just in case)
        if col_name not in sample_df.columns:
            continue

        # Get a sample of non-null values
        sample = sample_df[col_name].drop_nulls().to_list()

        # Skip if no samples
        if not sample:
            continue

        # Check if most values match date patterns
        date_count = sum(1 for val in sample if is_date_string(val))
        if date_count > len(sample) * threshold:  # If more than threshold% match date patterns
            print(f"Column '{col_name}' appears to contain date values ({date_count}/{len(sample)} match date patterns)")
            inferred_types[col_name] = 'datetime'

    return inferred_types

def extract_dataset_metadata(df: Union[pl.DataFrame, pl.LazyFrame], sample_size: int = 10000) -> Dict[str, Any]:
    """
    Extract metadata from a dataset including column information and possible aggregations.
    Optimized for large datasets using lazy evaluation and sampling.

    Args:
        df (Union[pl.DataFrame, pl.LazyFrame]): The DataFrame or LazyFrame to analyze
        sample_size (int, optional): Number of rows to sample for metadata generation

    Returns:
        Dict[str, Any]: A dictionary containing dataset metadata
    """
    import time
    start_time = time.time()

    # Convert to LazyFrame for optimized processing
    if isinstance(df, pl.DataFrame):
        lf = df.lazy()
    else:
        lf = df  # Already a LazyFrame

    # Get schema information without collecting
    schema = lf.schema
    columns = list(schema.keys())
    num_columns = len(columns)

    # Get row count using lazy evaluation
    num_rows_query = lf.select(pl.count())
    num_rows = num_rows_query.collect().item()

    # For large datasets, use sampling for metadata generation
    sampling_applied = False
    if num_rows > sample_size:
        print(f"Large dataset detected ({num_rows} rows). Using sampling for metadata generation.")
        sampled_df = lf.sample(sample_size, seed=42).collect()
        sampling_applied = True
    else:
        sampled_df = lf.collect()

    # Detect string columns that might contain dates
    print("Detecting date columns for metadata...")
    inferred_date_columns = detect_date_columns(sampled_df)

    # Get column metadata and possible aggregations
    columns_metadata = get_dataset_column_aggregations(sampled_df)

    # Update column metadata with inferred date types
    for col_name, inferred_type in inferred_date_columns.items():
        if col_name in columns_metadata:
            # Mark the column as a date column in the metadata
            columns_metadata[col_name]['inferred_data_type'] = inferred_type
            columns_metadata[col_name]['date_column'] = True

            # Add datetime aggregations to the available aggregations
            if 'available_aggregations' in columns_metadata[col_name]:
                columns_metadata[col_name]['available_aggregations'] = list(DATETIME_AGGREGATIONS.keys())

    # Calculate null counts efficiently using lazy evaluation
    null_count_expressions = [pl.col(col).null_count().alias(f"{col}_null") for col in columns]
    null_counts_result = lf.select(null_count_expressions).collect()

    # Convert to dictionary
    null_counts = {}
    for col in columns:
        null_counts[col] = null_counts_result[0, f"{col}_null"]

    total_null_count = sum(null_counts.values())

    # Estimate memory usage
    # For LazyFrames, we can't directly get the memory usage, so we estimate based on schema
    estimated_memory = 0
    for col, dtype in schema.items():
        # Rough estimates based on data type
        if dtype in (pl.Int8, pl.UInt8, pl.Boolean):
            bytes_per_value = 1
        elif dtype in (pl.Int16, pl.UInt16):
            bytes_per_value = 2
        elif dtype in (pl.Int32, pl.UInt32, pl.Float32):
            bytes_per_value = 4
        elif dtype in (pl.Int64, pl.UInt64, pl.Float64, pl.Date, pl.Time):
            bytes_per_value = 8
        elif dtype == pl.Datetime:
            bytes_per_value = 8
        elif dtype == pl.Utf8:
            # For strings, we use an average estimate
            bytes_per_value = 32
        else:
            bytes_per_value = 8  # Default estimate

        # Add to total estimate
        estimated_memory += num_rows * bytes_per_value

    # Add performance metrics
    end_time = time.time()
    execution_time = round(end_time - start_time, 3)

    # Create metadata dictionary
    metadata = {
        "dataset_info": {
            "num_rows": num_rows,
            "num_columns": num_columns,
            "total_null_count": total_null_count,
            "estimated_memory_bytes": estimated_memory,
            "inferred_date_columns": list(inferred_date_columns.keys()),
            "sampling_applied": sampling_applied,
            "sample_size": sample_size if sampling_applied else num_rows,
            "metadata_generation_time": execution_time
        },
        "columns": columns_metadata,
        "null_counts": null_counts
    }

    return metadata


def get_column_type_from_schema(schema: Dict[str, pl.DataType], column: str) -> str:
    """
    Determine the type of a column from a schema without loading the data.

    Args:
        schema (Dict[str, pl.DataType]): The schema of the DataFrame
        column (str): The name of the column

    Returns:
        str: The type of the column ('numeric', 'string', 'datetime', or 'unknown')
    """
    try:
        dtype = schema[column]

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
    except Exception:
        return 'unknown'

def create_time_period_expression(x_axis: str, agg_type: str) -> pl.Expr:
    """
    Create a Polars expression for time-based aggregation.

    Args:
        x_axis (str): The column name to use as x-axis
        agg_type (str): The type of time-based aggregation ('daily', 'monthly', 'quarterly', 'yearly')

    Returns:
        pl.Expr: A Polars expression for creating the time period column
    """
    if agg_type == 'daily':
        # Format: YYYY-MM-DD
        return pl.col(x_axis).dt.date().cast(pl.Utf8).alias('time_period')
    elif agg_type == 'monthly':
        # Format: YYYY-MM
        return (pl.col(x_axis).dt.year().cast(pl.Utf8) + "-" +
                pl.col(x_axis).dt.month().cast(pl.Utf8).str.zfill(2)).alias('time_period')
    elif agg_type == 'quarterly':
        # Calculate quarter (1-4) from month
        return (pl.col(x_axis).dt.year().cast(pl.Utf8) + "-Q" +
                ((pl.col(x_axis).dt.month() - 1) / 3 + 1).cast(pl.Int8).cast(pl.Utf8)).alias('time_period')
    elif agg_type == 'yearly':
        # Format: YYYY
        return pl.col(x_axis).dt.year().cast(pl.Utf8).alias('time_period')
    else:
        # Default to daily if aggregation type is not recognized
        return pl.col(x_axis).dt.date().cast(pl.Utf8).alias('time_period')

def get_aggregation_expression(column: str, agg_type: str) -> pl.Expr:
    """
    Get the appropriate Polars aggregation expression for a column and aggregation type.

    Args:
        column (str): The column name to aggregate
        agg_type (str): The type of aggregation

    Returns:
        pl.Expr: A Polars aggregation expression
    """
    if agg_type == 'sum':
        return pl.col(column).sum().alias(column)
    elif agg_type == 'mean':
        return pl.col(column).mean().alias(column)
    elif agg_type == 'min':
        return pl.col(column).min().alias(column)
    elif agg_type == 'max':
        return pl.col(column).max().alias(column)
    elif agg_type == 'count':
        return pl.col(column).count().alias(column)
    elif agg_type == 'median':
        return pl.col(column).median().alias(column)
    elif agg_type == 'std':
        return pl.col(column).std().alias(column)
    elif agg_type == 'var':
        return pl.col(column).var().alias(column)
    elif agg_type == 'unique_count':
        return pl.col(column).n_unique().alias(column)
    else:
        # Default to count for unknown aggregation types
        return pl.col(column).count().alias(column)

def perform_axis_based_aggregation(df: Union[pl.DataFrame, pl.LazyFrame], x_axis: str, y_axis: Union[str, List[str]],
                             x_axis_aggregations: Dict[str, str] = None,
                             y_axis_aggregations: Dict[str, str] = None,
                             max_unique_values: int = 1000,
                             sample_size: int = None) -> Dict[str, Any]:
    """
    Perform aggregations based on column data types and axis roles (x-axis or y-axis).
    Optimized for large datasets using lazy evaluation.

    This function handles different aggregation strategies based on whether columns are used
    as x-axis or y-axis in visualizations, with special handling for datetime columns.

    Args:
        df (Union[pl.DataFrame, pl.LazyFrame]): The DataFrame or LazyFrame to aggregate
        x_axis (str): The column name to use as x-axis
        y_axis (Union[str, List[str]]): The column name(s) to use as y-axis
        x_axis_aggregations (Dict[str, str], optional): Aggregations to apply to x-axis column
        y_axis_aggregations (Dict[str, str], optional): Aggregations to apply to y-axis columns
        max_unique_values (int, optional): Maximum number of unique values to process for x-axis
        sample_size (int, optional): Number of rows to sample for large datasets

    Returns:
        Dict[str, Any]: A dictionary containing the aggregated data and metadata
    """
    # Start timing for performance metrics
    import time
    start_time = time.time()

    # Convert to LazyFrame for optimized processing
    if isinstance(df, pl.DataFrame):
        lf = df.lazy()
    else:
        lf = df  # Already a LazyFrame

    # Apply sampling if requested (for very large datasets)
    if sample_size is not None:
        total_rows = lf.select(pl.count()).collect().item()
        if total_rows > sample_size:
            print(f"Sampling {sample_size} rows from {total_rows} total rows")
            lf = lf.sample(sample_size, seed=42)

    # Get schema information without collecting
    schema = lf.schema

    # Initialize result structure
    result = {
        "chart_data": {
            "labels": [],
            "datasets": []
        },
        "metadata": {
            "x_axis": {
                "column": x_axis,
                "type": get_column_type_from_schema(schema, x_axis),
                "aggregation": x_axis_aggregations.get(x_axis) if x_axis_aggregations else None
            },
            "y_axes": [],
            "performance": {}
        }
    }

    # Convert y_axis to list if it's a single string
    y_axes = y_axis if isinstance(y_axis, list) else [y_axis]

    # Process x-axis aggregation if provided
    x_agg = x_axis_aggregations.get(x_axis) if x_axis_aggregations else None
    x_axis_type = get_column_type_from_schema(schema, x_axis)

    # Create a working LazyFrame - avoid modifying the original
    working_lf = lf

    # Handle time-based aggregation for x-axis
    if x_agg in ['daily', 'monthly', 'quarterly', 'yearly'] and x_axis_type == 'datetime':
        # Create a temporary column with the time periods based on aggregation type
        time_period_expr = create_time_period_expression(x_axis, x_agg)
        working_lf = working_lf.with_columns(time_period_expr)

        # Replace the x_axis with the time_period column for grouping
        x_axis = 'time_period'
        result["metadata"]["x_axis"]["aggregation_type"] = x_agg

    # Get unique values for x-axis to use as labels - limit to max_unique_values
    x_axis_unique = working_lf.select(pl.col(x_axis).unique().sort()).collect()
    x_axis_labels = x_axis_unique[x_axis].to_list()

    # Check if we have too many unique values
    if len(x_axis_labels) > max_unique_values:
        print(f"Warning: X-axis has {len(x_axis_labels)} unique values, limiting to {max_unique_values}")
        # For large number of unique values, we'll need to filter or bin the data
        # For now, just take the first max_unique_values
        x_axis_labels = x_axis_labels[:max_unique_values]
        # Filter the working LazyFrame to only include these values
        working_lf = working_lf.filter(pl.col(x_axis).is_in(x_axis_labels))

    result["chart_data"]["labels"] = x_axis_labels

    # Generate a color palette for the datasets
    colors = [
        {"bg": "rgba(54, 162, 235, 0.5)", "border": "rgba(54, 162, 235, 1)"},
        {"bg": "rgba(255, 99, 132, 0.5)", "border": "rgba(255, 99, 132, 1)"},
        {"bg": "rgba(255, 206, 86, 0.5)", "border": "rgba(255, 206, 86, 1)"},
        {"bg": "rgba(75, 192, 192, 0.5)", "border": "rgba(75, 192, 192, 1)"},
        {"bg": "rgba(153, 102, 255, 0.5)", "border": "rgba(153, 102, 255, 1)"},
        {"bg": "rgba(255, 159, 64, 0.5)", "border": "rgba(255, 159, 64, 1)"},
        {"bg": "rgba(201, 203, 207, 0.5)", "border": "rgba(201, 203, 207, 1)"}
    ]

    # Prepare aggregation expressions for all y-axes at once
    agg_expressions = []
    for y_var in y_axes:
        y_agg = y_axis_aggregations.get(y_var) if y_axis_aggregations else None
        y_axis_type = get_column_type_from_schema(schema, y_var)

        # Add y-axis metadata
        y_axis_meta = {
            "column": y_var,
            "type": y_axis_type,
            "aggregation": y_agg
        }
        result["metadata"]["y_axes"].append(y_axis_meta)

        # Check if this is a time-based aggregation on a date column
        if y_agg in ['daily', 'monthly', 'quarterly', 'yearly'] and y_axis_type == 'datetime':
            # Time-based aggregations for y-axis are handled separately
            continue

        # Determine the aggregation to use
        if not y_agg:
            # No aggregation specified, use default based on column type
            if y_axis_type == 'numeric':
                y_agg = 'mean'
            else:
                y_agg = 'count'

        # Create the aggregation expression
        agg_expr = get_aggregation_expression(y_var, y_agg)
        agg_expressions.append(agg_expr)

    # Process each y-axis variable
    for i, y_var in enumerate(y_axes):
        y_agg = y_axis_aggregations.get(y_var) if y_axis_aggregations else None
        y_axis_type = get_column_type_from_schema(schema, y_var)

        # Check if this is a time-based aggregation on a date column
        if y_agg in ['daily', 'monthly', 'quarterly', 'yearly'] and y_axis_type == 'datetime':
            # Use the time-based aggregation function
            time_agg_result = perform_time_based_aggregation(working_lf.collect(), y_var, y_agg)

            # Create dataset for time-based aggregation
            dataset = {
                "label": f"{time_agg_result['type']} Distribution of {y_var}",
                "data": time_agg_result["counts"],
                "backgroundColor": colors[i % len(colors)]["bg"],
                "borderColor": colors[i % len(colors)]["border"],
                "borderWidth": 1,
                "time_aggregation": {
                    "type": y_agg,
                    "periods": time_agg_result["periods"]
                }
            }

            result["chart_data"]["datasets"].append(dataset)
            continue

        # Set default aggregation if not specified
        if not y_agg:
            if y_axis_type == 'numeric':
                y_agg = 'mean'
            else:
                y_agg = 'count'

        # Execute the aggregation query
        agg_expr = get_aggregation_expression(y_var, y_agg)
        agg_result = working_lf.group_by(x_axis).agg(agg_expr).collect()

        # Sort the result by x-axis
        agg_result = agg_result.sort(x_axis)

        # Ensure all x-axis labels have corresponding y values
        y_values = []
        for label in x_axis_labels:
            row = agg_result.filter(pl.col(x_axis) == label)
            if row.height > 0:
                y_values.append(row[0, y_var])
            else:
                y_values.append(0)  # Use 0 for missing values

        # Create dataset label
        dataset_label = f"{y_agg} of {y_var}"
        if x_agg in ['daily', 'monthly', 'quarterly', 'yearly']:
            dataset_label = f"{dataset_label} ({x_agg})"

        # Create dataset
        dataset = {
            "label": dataset_label,
            "data": y_values,
            "backgroundColor": colors[i % len(colors)]["bg"],
            "borderColor": colors[i % len(colors)]["border"],
            "borderWidth": 1
        }

        result["chart_data"]["datasets"].append(dataset)

    # Add performance metrics
    end_time = time.time()
    result["metadata"]["performance"] = {
        "execution_time_seconds": round(end_time - start_time, 3),
        "sampling_applied": sample_size is not None,
        "sample_size": sample_size
    }

    return result

# For large datasets, consider using Polars' lazy API (pl.LazyFrame) to optimize performance.

            # # Perform the aggregations
            # result = (
            #     lf.group_by(pl.col("date").dt.year().alias("year"))  # Group by year
            #     .agg(aggregations)                                   # Apply the aggregations
            #     .collect()                                           # Execute the query
            # )

            # # Print the result
            # print(result)