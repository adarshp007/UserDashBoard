# Aggregations for the numerical column
# result = {
#     "mean": df["values"].mean(),
#     "sum": df["values"].sum(),
#     "min": df["values"].min(),
#     "max": df["values"].max(),
#     "count": df["values"].count(),
#     "median": df["values"].median(),
#     "std": df["values"].std(),
#     "var": df["values"].var(),
#     "skew": df["values"].skew(),
#     "kurtosis": df["values"].kurtosis(),
#     "25th_percentile": df["values"].quantile(0.25),
#     "75th_percentile": df["values"].quantile(0.75),
#     "range": df["values"].max() - df["values"].min(),
#     "iqr": df["values"].quantile(0.75) - df["values"].quantile(0.25),
#     "null_count": df["values"].is_null().sum(),
#     "non_null_count": df["values"].count(),
#     "cumulative_sum": df["values"].cumsum().to_list(),
#     "rolling_mean": df["values"].rolling_mean(window_size=3).to_list()
# }

# Aggregations for the string column
# result = {
#     "unique_count": df["fruits"].n_unique(),
#     "most_frequent": df["fruits"].mode().get(0, None),
#     "value_counts": df["fruits"].value_counts(),
#     "min_value": df["fruits"].min(),
#     "max_value": df["fruits"].max(),
#     "mean_length": df["fruits"].str.lengths().mean(),
#     "null_count": df["fruits"].is_null().sum(),
#     "empty_count": (df["fruits"].str.lengths() == 0).sum(),
#     "contains_apple": df["fruits"].str.contains("apple").sum(),
#     "is_unique": df["fruits"].n_unique() == df["fruits"].len()
# }

# Aggregations for the datetime column
# result = {
#     "min_date": df["timestamps"].min(),
#     "max_date": df["timestamps"].max(),
#     "count": df["timestamps"].count(),
#     "time_span": df["timestamps"].max() - df["timestamps"].min(),
#     "avg_diff": df["timestamps"].diff().mean(),
#     "unique_days": df["timestamps"].dt.day().n_unique(),
#     "unique_months": df["timestamps"].dt.month().n_unique(),
#     "unique_years": df["timestamps"].dt.year().n_unique(),
#     "most_frequent": df["timestamps"].mode().get(0, None),
#     "null_count": df["timestamps"].is_null().sum(),
#     "non_null_count": df["timestamps"].count(),
#     "rolling_count": df["timestamps"].rolling_count(window_size="3d").to_list()
# }






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