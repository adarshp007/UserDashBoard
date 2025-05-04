import requests
import json
import os
import time

# Base URLs for the API
CREATE_DATASET_URL = "http://localhost:8000/dashboard/createdataset/"
STATUS_URL = "http://localhost:8000/dashboard/dataset-status/"

def test_create_dataset_async():
    """Test the asynchronous dataset creation endpoint."""

    # Replace with the path to your test file
    file_path = "path/to/your/test_file.xlsx"

    if not os.path.exists(file_path):
        print(f"Test file not found at {file_path}")
        print("Please update the file_path variable with a valid Excel file path.")
        return

    # Prepare the multipart form data
    files = {
        'file': open(file_path, 'rb')
    }

    data = {
        'name': 'Test Dataset',
        'description': 'A test dataset created via API'
    }

    # Send the request to create the dataset
    print("Creating dataset...")
    response = requests.post(CREATE_DATASET_URL, files=files, data=data)
    print("Response Status:", response.status_code)

    if response.status_code == 202:  # Accepted
        result = response.json()

        # Print basic info
        print("\nDataset Creation Initiated:")
        print(f"Name: {result['dataset']['name']}")
        print(f"Description: {result['dataset']['description']}")
        print(f"Dataset ID: {result['dataset_id']}")
        print(f"Status: {result['status']}")
        print(f"Message: {result['message']}")

        # Poll the status endpoint to check when processing is complete
        dataset_id = result['dataset_id']
        status_url = f"{STATUS_URL}{dataset_id}/"

        print("\nPolling for dataset status...")
        max_attempts = 10
        attempt = 0

        while attempt < max_attempts:
            attempt += 1
            print(f"\nChecking status (attempt {attempt}/{max_attempts})...")

            try:
                status_response = requests.get(status_url)

                if status_response.status_code == 200:
                    status_result = status_response.json()
                    print(f"Current Status: {status_result['status']}")

                    if status_result['status'] == "READ_COMPLETE":
                        print("\nDataset processing completed successfully!")

                        # Print dataset info if available
                        if "dataset_info" in status_result:
                            print("\nDataset Info:")
                            dataset_info = status_result["dataset_info"]
                            print(f"Number of Rows: {dataset_info.get('num_rows', 'N/A')}")
                            print(f"Number of Columns: {dataset_info.get('num_columns', 'N/A')}")
                            print(f"Total Null Count: {dataset_info.get('total_null_count', 'N/A')}")

                        # Print column information if available
                        if "columns" in status_result:
                            print("\nColumn Information (sample):")
                            columns = status_result["columns"]
                            # Print just a few columns as a sample
                            for i, (column_name, column_info) in enumerate(columns.items()):
                                if i >= 3:  # Limit to 3 columns for brevity
                                    print(f"\n... and {len(columns) - 3} more columns")
                                    break

                                print(f"\n{column_name}:")
                                print(f"  Data Type: {column_info['data_type']}")
                                print(f"  Available Aggregations: {', '.join(column_info['available_aggregations'][:5])}...")

                        break
                    elif status_result['status'] == "READ_FAILED":
                        print("\nDataset processing failed!")
                        break

                    # If still processing, wait and try again
                    print("Dataset still processing, waiting...")
                    time.sleep(5)  # Wait 5 seconds before checking again
                else:
                    print(f"Error checking status: {status_response.status_code}")
                    print(status_response.json())
                    break
            except Exception as e:
                print(f"Error checking status: {str(e)}")
                break

        if attempt >= max_attempts:
            print("\nMax polling attempts reached. Dataset may still be processing.")
            print(f"You can check the status later at: {status_url}")
    else:
        print("Error Response:", response.json())

if __name__ == "__main__":
    print("Testing asynchronous dataset creation endpoint...")
    test_create_dataset_async()
