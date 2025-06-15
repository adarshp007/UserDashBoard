import json

import requests

# Base URL for the API
BASE_URL = "http://localhost:8000/dashboard/dataset-columns/"


def test_dataset_column_aggregations():
    """Test the POST endpoint to get available aggregations for each column in a dataset."""
    # Sample request data
    data = {
        "file_name": "Employment_to_population_ratio_for_residents_in_the_Emirate_of_Abu_Dhabi_by_region_and_gender_-_quarterly.csv_(2).xlsx"
    }

    # Send the request
    response = requests.post(BASE_URL, json=data)
    print("POST Response Status:", response.status_code)

    if response.status_code == 200:
        result = response.json()

        # Print dataset info
        print("\nDataset Info:")
        print(f"File Name: {result['dataset_info']['file_name']}")
        print(f"Number of Columns: {result['dataset_info']['num_columns']}")
        print(f"Number of Rows: {result['dataset_info']['num_rows']}")

        # Print column information
        print("\nColumn Information:")
        for column_name, column_info in result["columns"].items():
            print(f"\n{column_name}:")
            print(f"  Data Type: {column_info['data_type']}")
            print(f"  Polars Type: {column_info['polars_type']}")
            print(f"  Sample Data: {column_info['sample_data'][:3]}...")
            print(f"  Available Aggregations: {', '.join(column_info['available_aggregations'])}")
    else:
        print("Error Response:", response.json())


if __name__ == "__main__":
    print("Testing POST endpoint to get dataset column aggregations...")
    test_dataset_column_aggregations()
