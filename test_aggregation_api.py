import json
import uuid

import requests

# Base URL for the API
BASE_URL = "http://localhost:8000/dashboard/aggregations/"


def test_get_available_aggregations():
    """Test the GET endpoint to retrieve available aggregation functions."""
    response = requests.get(BASE_URL)
    print("GET Response Status:", response.status_code)
    print("GET Response Content:")
    print(json.dumps(response.json(), indent=2))
    print("\n" + "-" * 50 + "\n")


def test_perform_aggregations():
    """Test the POST endpoint to perform aggregations on a dataset."""
    # Sample request data
    data = {
        "file_name": "Employment_to_population_ratio_for_residents_in_the_Emirate_of_Abu_Dhabi_by_region_and_gender_-_quarterly.csv_(2).xlsx",
        "aggregations": {"Year": ["min", "max", "unique_count"], "Total": ["mean", "sum", "min", "max", "median"]},
    }

    # Send the request
    response = requests.post(BASE_URL, json=data)
    print("POST Response Status:", response.status_code)
    print("POST Response Content:")
    print(json.dumps(response.json(), indent=2))


if __name__ == "__main__":
    print("Testing GET endpoint to retrieve available aggregation functions...")
    test_get_available_aggregations()

    print("Testing POST endpoint to perform aggregations...")
    test_perform_aggregations()
