# User Dashboard

A Django application for managing user dashboards with advanced data visualization and aggregation capabilities. This application allows users to upload, process, and visualize datasets through an intuitive web interface.

## Features

### Data Management
- Upload and process CSV and Excel (XLSX) files
- Automatic conversion to optimized Parquet format for faster processing
- Background processing of large files using Celery
- Secure file storage using Minio (S3-compatible storage)
- Dataset metadata extraction and storage

### Data Visualization
- Interactive chart generation with multiple chart types (bar, line, pie, scatter)
- Support for single and multiple Y-axis variables
- Customizable aggregation settings for both X and Y axes
- Time-based aggregations for date columns (daily, monthly, quarterly, yearly)
- Filtering capabilities to focus on specific data subsets

### User Interface
- Clean, responsive dashboard interface
- Dataset list view with status indicators
- Detailed dataset view showing columns and available aggregations
- Interactive visualization form with dynamic options based on data types
- Real-time feedback on aggregation selections

## Docker Setup

### Prerequisites

- Docker
- Docker Compose

### Getting Started

1. Clone the repository:
   ```
   git clone <repository-url>
   cd UserDashBoard
   ```

2. Create a `.env` file from the example:
   ```
   cp .env.example .env
   ```

3. Update the `.env` file with your configuration values.

4. Build and start the Docker containers:
   ```
   docker-compose up -d --build
   ```

5. Create a superuser (optional):
   ```
   docker-compose exec web python manage.py createsuperuser
   ```

6. Access the application:
   - Web interface: http://localhost:8000
   - Admin interface: http://localhost:8000/admin

### Docker Commands

- Start the containers:
  ```
  docker-compose up -d
  ```

- Stop the containers:
  ```
  docker-compose down
  ```

- View logs:
  ```
  docker-compose logs -f
  ```

- Run Django management commands:
  ```
  docker-compose exec web python manage.py <command>
  ```

## API Endpoints

### Dataset Management
- `POST /dashboard/api/datasets/`: Upload and create a new dataset
- `GET /dashboard/api/datasets/`: List all datasets
- `GET /dashboard/api/datasets/<uuid:dataset_id>/`: Get dataset details
- `DELETE /dashboard/api/datasets/<uuid:dataset_id>/`: Delete a dataset
- `GET /dashboard/api/datasets/<uuid:dataset_id>/status/`: Check the status of a dataset

### Data Analysis
- `POST /dashboard/api/datasets/<uuid:dataset_id>/aggregations/`: Perform aggregations on a dataset
- `GET /dashboard/api/datasets/<uuid:dataset_id>/columns/`: Get available aggregations for each column in a dataset
- `POST /dashboard/api/datasets/<uuid:dataset_id>/visualize/`: Generate visualization data based on selected variables and aggregations

### Web Interface
- `GET /dashboard/datasets/`: View list of all datasets
- `GET /dashboard/datasets/<uuid:dataset_id>/`: View dataset details and visualization interface
- `GET /dashboard/upload/`: Access the file upload interface

## Development

### Local Setup

1. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```
   cp .env.example .env
   ```

4. Run migrations:
   ```
   python manage.py migrate
   ```

5. Start the development server:
   ```
   python manage.py runserver
   ```

6. Start Celery worker (in a separate terminal):
   ```
   celery -A userdashboard worker --loglevel=info
   ```

## Using the Visualization Features

### Uploading a Dataset
1. Navigate to the upload page at `/dashboard/upload/`
2. Select a CSV or Excel file from your computer
3. Provide a name and optional description for the dataset
4. Click "Upload" to start the upload and processing
5. The system will automatically extract metadata and identify column types

### Creating Visualizations
1. From the datasets list, click on a dataset to view its details
2. In the visualization section:
   - Select one or more variables for the X-axis
   - Select one or more variables for the Y-axis
   - Choose a chart type (bar, line, pie, scatter)
   - Optionally set filters to focus on specific data

3. Configure aggregation settings:
   - For each X-axis variable, select an appropriate aggregation
   - For each Y-axis variable, select an appropriate aggregation
   - Available aggregations depend on the column type:
     - Numeric columns: sum, mean, min, max, median, etc.
     - Date columns: daily, monthly, quarterly, yearly aggregations
     - String columns: count, first, last, etc.

4. Click "Generate Visualization" to create the chart
5. The visualization will display with a summary of the data and applied aggregations

### Working with Aggregations
- **No Aggregation**: Uses raw data values (with automatic grouping for categorical X-axis)
- **Sum**: Calculates the sum of values for each group
- **Mean**: Calculates the average of values for each group
- **Min/Max**: Shows the minimum or maximum value in each group
- **Count**: Counts the number of occurrences in each group
- **Time-based**: Groups date/time data by the specified period

### Tips for Effective Visualizations
- Choose appropriate chart types for your data:
  - Bar charts: Good for comparing categories
  - Line charts: Best for showing trends over time
  - Pie charts: Useful for showing proportions of a whole
  - Scatter plots: Ideal for showing relationships between variables
- Use aggregations to simplify complex datasets
- Apply filters to focus on specific subsets of data
- For time series data, use time-based aggregations to identify trends

## Technical Architecture

### Backend Components
- **Django**: Web framework for handling HTTP requests and responses
- **Django REST Framework**: API framework for building RESTful endpoints
- **Celery**: Distributed task queue for background processing
- **Redis**: Message broker for Celery and caching
- **Polars**: High-performance data processing library for dataset operations
- **Minio**: S3-compatible object storage for file storage

### Frontend Components
- **Bootstrap 5**: CSS framework for responsive UI components
- **Chart.js**: JavaScript library for interactive data visualizations
- **jQuery**: JavaScript library for DOM manipulation and AJAX requests

### Data Flow
1. User uploads a file through the web interface
2. File is temporarily stored and a Celery task is created
3. Celery worker processes the file:
   - Converts to Parquet format
   - Extracts metadata
   - Stores in Minio
4. User selects visualization parameters
5. Backend retrieves data from Minio, applies aggregations, and returns results
6. Frontend renders the visualization using Chart.js

## Conclusion

The User Dashboard application provides a powerful yet user-friendly interface for data visualization and analysis. By combining modern web technologies with efficient data processing libraries, it enables users to gain insights from their datasets without requiring specialized technical knowledge.

The application is designed to be scalable and extensible, with a modular architecture that allows for easy addition of new features and capabilities. The use of containerization through Docker ensures consistent deployment across different environments.