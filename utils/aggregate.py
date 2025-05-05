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

def perform_time_based_aggregation(df: pl.DataFrame, date_column: str, aggregation_type: str) -> Dict[str, Any]:
    """
    Perform time-based aggregation on a date column.

    Args:
        df (pl.DataFrame): The DataFrame to aggregate
        date_column (str): The name of the date column
        aggregation_type (str): The type of time-based aggregation ('daily', 'monthly', 'quarterly', 'yearly')

    Returns:
        Dict[str, Any]: A dictionary with time periods as keys and counts as values
    """
    try:
        # Make sure we're working with a datetime column
        if get_column_type(df, date_column) != 'datetime':
            return {"error": f"Column {date_column} is not a datetime column"}

        # Create a copy of the DataFrame to avoid modifying the original
        date_df = df.clone()

        # Create the appropriate time period column based on aggregation type
        if aggregation_type == 'daily':
            # Format: YYYY-MM-DD
            date_df = date_df.with_columns(
                pl.col(date_column).dt.date().cast(pl.Utf8).alias('time_period')
            )
            period_format = "Daily"
        elif aggregation_type == 'monthly':
            # Format: YYYY-MM
            date_df = date_df.with_columns(
                (pl.col(date_column).dt.year().cast(pl.Utf8) + "-" +
                 pl.col(date_column).dt.month().cast(pl.Utf8).str.zfill(2)).alias('time_period')
            )
            period_format = "Monthly"
        elif aggregation_type == 'quarterly':
            # Calculate quarter (1-4) from month
            date_df = date_df.with_columns(
                (pl.col(date_column).dt.year().cast(pl.Utf8) + "-Q" +
                 ((pl.col(date_column).dt.month() - 1) / 3 + 1).cast(pl.Int8).cast(pl.Utf8)).alias('time_period')
            )
            period_format = "Quarterly"
        elif aggregation_type == 'yearly':
            # Format: YYYY
            date_df = date_df.with_columns(
                pl.col(date_column).dt.year().cast(pl.Utf8).alias('time_period')
            )
            period_format = "Yearly"
        else:
            return {"error": f"Unsupported aggregation type: {aggregation_type}"}

        # Group by the time period and count
        agg_result = date_df.group_by('time_period').agg(
            pl.count().alias('count')
        ).sort('time_period')

        # Convert to dictionary for the response
        time_periods = agg_result['time_period'].to_list()
        counts = agg_result['count'].to_list()

        # Create a structured response
        result = {
            "type": period_format,
            "data": dict(zip(time_periods, counts)),
            "periods": time_periods,
            "counts": counts
        }

        return result
    except Exception as e:
        return {"error": f"Error performing {aggregation_type} aggregation: {str(e)}"}

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

def detect_date_columns(df: pl.DataFrame) -> Dict[str, str]:
    """
    Detect string columns that might contain dates and return their inferred data types.

    Args:
        df (pl.DataFrame): The DataFrame to analyze

    Returns:
        Dict[str, str]: A dictionary mapping column names to their inferred data types
    """
    import re

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

    # Function to check if a string matches any date pattern
    def is_date_string(s):
        if not isinstance(s, str):
            return False
        return any(re.match(pattern, s) for pattern in date_patterns)

    inferred_types = {}

    # Check each string column
    for col_name in df.columns:
        if df.schema[col_name] == pl.Utf8:  # Only check string columns
            # Get a sample of non-null values
            sample = df[col_name].drop_nulls().head(100).to_list()

            # Skip if no samples
            if not sample:
                continue

            # Check if most values match date patterns
            date_count = sum(1 for val in sample if is_date_string(val))
            if date_count > len(sample) * 0.8:  # If more than 80% match date patterns
                print(f"Column '{col_name}' appears to contain date values")
                inferred_types[col_name] = 'datetime'

    return inferred_types

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

    # Detect string columns that might contain dates
    print("Detecting date columns for metadata...")
    inferred_date_columns = detect_date_columns(df)

    # Get column metadata and possible aggregations
    columns_metadata = get_dataset_column_aggregations(df)

    # Update column metadata with inferred date types
    for col_name, inferred_type in inferred_date_columns.items():
        if col_name in columns_metadata:
            # Mark the column as a date column in the metadata
            columns_metadata[col_name]['inferred_data_type'] = inferred_type
            columns_metadata[col_name]['date_column'] = True

            # Add datetime aggregations to the available aggregations
            if 'available_aggregations' in columns_metadata[col_name]:
                columns_metadata[col_name]['available_aggregations'] = list(DATETIME_AGGREGATIONS.keys())

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
            "inferred_date_columns": list(inferred_date_columns.keys())
        },
        "columns": columns_metadata,
        "null_counts": null_counts
    }

    return metadata


def perform_axis_based_aggregation(df: pl.DataFrame, x_axis: str, y_axis: Union[str, List[str]],
                             x_axis_aggregations: Dict[str, str] = None,
                             y_axis_aggregations: Dict[str, str] = None) -> Dict[str, Any]:
    """
    Perform aggregations based on column data types and axis roles (x-axis or y-axis).

    This function handles different aggregation strategies based on whether columns are used
    as x-axis or y-axis in visualizations, with special handling for datetime columns.

    Args:
        df (pl.DataFrame): The DataFrame to aggregate
        x_axis (str): The column name to use as x-axis
        y_axis (Union[str, List[str]]): The column name(s) to use as y-axis
        x_axis_aggregations (Dict[str, str], optional): Aggregations to apply to x-axis column
        y_axis_aggregations (Dict[str, str], optional): Aggregations to apply to y-axis columns

    Returns:
        Dict[str, Any]: A dictionary containing the aggregated data and metadata
    """
    # Ensure we're working with a DataFrame, not a LazyFrame
    if isinstance(df, pl.LazyFrame):
        df = df.collect()

    # Initialize result structure
    result = {
        "chart_data": {
            "labels": [],
            "datasets": []
        },
        "metadata": {
            "x_axis": {
                "column": x_axis,
                "type": get_column_type(df, x_axis),
                "aggregation": x_axis_aggregations.get(x_axis) if x_axis_aggregations else None
            },
            "y_axes": []
        }
    }

    # Convert y_axis to list if it's a single string
    y_axes = y_axis if isinstance(y_axis, list) else [y_axis]

    # Process x-axis aggregation if provided
    x_agg = x_axis_aggregations.get(x_axis) if x_axis_aggregations else None
    x_axis_type = get_column_type(df, x_axis)
    working_df = df.clone()  # Create a copy to avoid modifying the original

    # Handle time-based aggregation for x-axis
    if x_agg in ['daily', 'monthly', 'quarterly', 'yearly'] and x_axis_type == 'datetime':
        # Create a temporary column with the time periods based on aggregation type
        if x_agg == 'daily':
            # Format: YYYY-MM-DD
            working_df = working_df.with_columns(
                pl.col(x_axis).dt.date().cast(pl.Utf8).alias('time_period')
            )
        elif x_agg == 'monthly':
            # Format: YYYY-MM
            working_df = working_df.with_columns(
                (pl.col(x_axis).dt.year().cast(pl.Utf8) + "-" +
                pl.col(x_axis).dt.month().cast(pl.Utf8).str.zfill(2)).alias('time_period')
            )
        elif x_agg == 'quarterly':
            # Calculate quarter (1-4) from month
            working_df = working_df.with_columns(
                (pl.col(x_axis).dt.year().cast(pl.Utf8) + "-Q" +
                ((pl.col(x_axis).dt.month() - 1) / 3 + 1).cast(pl.Int8).cast(pl.Utf8)).alias('time_period')
            )
        elif x_agg == 'yearly':
            # Format: YYYY
            working_df = working_df.with_columns(
                pl.col(x_axis).dt.year().cast(pl.Utf8).alias('time_period')
            )

        # Replace the x_axis with the time_period column for grouping
        x_axis = 'time_period'
        result["metadata"]["x_axis"]["aggregation_type"] = x_agg

    # Get unique values for x-axis to use as labels
    x_axis_labels = working_df[x_axis].unique().sort().to_list()
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

    # Process each y-axis variable
    for i, y_var in enumerate(y_axes):
        y_agg = y_axis_aggregations.get(y_var) if y_axis_aggregations else None
        y_axis_type = get_column_type(working_df, y_var)

        # Add y-axis metadata
        y_axis_meta = {
            "column": y_var,
            "type": y_axis_type,
            "aggregation": y_agg
        }
        result["metadata"]["y_axes"].append(y_axis_meta)

        # Check if this is a time-based aggregation on a date column
        if y_agg in ['daily', 'monthly', 'quarterly', 'yearly'] and y_axis_type == 'datetime':
            # Use the time-based aggregation function
            time_agg_result = perform_time_based_aggregation(working_df, y_var, y_agg)

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

        # Perform aggregation based on column type and specified aggregation
        if y_agg:
            # Group by x-axis and aggregate y-axis
            if y_agg == 'sum':
                agg_result = working_df.group_by(x_axis).agg(pl.col(y_var).sum().alias(y_var))
            elif y_agg == 'mean':
                agg_result = working_df.group_by(x_axis).agg(pl.col(y_var).mean().alias(y_var))
            elif y_agg == 'min':
                agg_result = working_df.group_by(x_axis).agg(pl.col(y_var).min().alias(y_var))
            elif y_agg == 'max':
                agg_result = working_df.group_by(x_axis).agg(pl.col(y_var).max().alias(y_var))
            elif y_agg == 'count':
                agg_result = working_df.group_by(x_axis).agg(pl.col(y_var).count().alias(y_var))
            elif y_agg == 'median':
                agg_result = working_df.group_by(x_axis).agg(pl.col(y_var).median().alias(y_var))
            elif y_agg == 'std':
                agg_result = working_df.group_by(x_axis).agg(pl.col(y_var).std().alias(y_var))
            elif y_agg == 'var':
                agg_result = working_df.group_by(x_axis).agg(pl.col(y_var).var().alias(y_var))
            elif y_agg == 'unique_count':
                agg_result = working_df.group_by(x_axis).agg(pl.col(y_var).n_unique().alias(y_var))
            elif y_agg == 'most_frequent':
                # For most_frequent, we need to use a different approach
                counts = working_df.group_by([x_axis, y_var]).count()
                agg_result = counts.sort(by=["count"], descending=True).group_by(x_axis).first()
            else:
                # For any other aggregation, fall back to count
                agg_result = working_df.group_by(x_axis).agg(pl.col(y_var).count().alias(y_var))
        else:
            # No aggregation specified, use default based on column type
            if y_axis_type == 'numeric':
                agg_result = working_df.group_by(x_axis).agg(pl.col(y_var).mean().alias(y_var))
                y_agg = 'mean'  # Set default aggregation
            elif y_axis_type == 'datetime':
                agg_result = working_df.group_by(x_axis).agg(pl.col(y_var).count().alias(y_var))
                y_agg = 'count'  # Set default aggregation
            else:
                agg_result = working_df.group_by(x_axis).agg(pl.col(y_var).count().alias(y_var))
                y_agg = 'count'  # Set default aggregation

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