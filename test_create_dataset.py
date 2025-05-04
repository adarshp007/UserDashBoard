import requests
import json
import os

# Base URL for the API
BASE_URL = "http://localhost:8000/dashboard/createdataset/"

def test_create_dataset():
    """Test the dataset creation endpoint with metadata extraction."""
    
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
    
    # Send the request
    response = requests.post(BASE_URL, files=files, data=data)
    print("Response Status:", response.status_code)
    
    if response.status_code == 201:
        result = response.json()
        
        # Print basic info
        print("\nDataset Created Successfully:")
        print(f"Name: {result['dataset']['name']}")
        print(f"Description: {result['dataset']['description']}")
        print(f"File URL: {result['file_url']}")
        
        # Print dataset info
        print("\nDataset Info:")
        print(f"Number of Rows: {result['dataset_info']['num_rows']}")
        print(f"Number of Columns: {result['dataset_info']['num_columns']}")
        print(f"Total Null Count: {result['dataset_info']['total_null_count']}")
        
        # Print column information
        print("\nColumn Information:")
        for column_name, column_info in result['columns'].items():
            print(f"\n{column_name}:")
            print(f"  Data Type: {column_info['data_type']}")
            print(f"  Polars Type: {column_info['polars_type']}")
            print(f"  Sample Data: {column_info['sample_data'][:3]}...")
            print(f"  Available Aggregations: {', '.join(column_info['available_aggregations'])}")
    else:
        print("Error Response:", response.json())

if __name__ == "__main__":
    print("Testing dataset creation endpoint with metadata extraction...")
    test_create_dataset()
