import os
import logging
from celery import shared_task
from Account.models import Dataset, User
from utils.backblaze import upload_file_to_b2
from utils.aggregate import extract_dataset_metadata
from django.shortcuts import get_object_or_404

logger = logging.getLogger(__name__)

@shared_task
def process_dataset_file(file_path, clean_filename, dataset_id):
    """
    Process a dataset file in the background:
    1. Upload the file to Backblaze
    2. Extract metadata
    3. Update the dataset with the metadata
    
    Args:
        file_path (str): Path to the temporary file
        clean_filename (str): Cleaned filename
        dataset_id (str): UUID of the dataset to update
    """
    try:
        logger.info(f"Starting background processing of dataset {dataset_id}")
        
        # Upload file to Backblaze and extract metadata
        result = upload_file_to_b2(file_path, clean_filename, extract_metadata=True)
        
        # Get the dataset
        dataset = Dataset.objects.get(object_id=dataset_id)
        
        # Update dataset with metadata and status
        dataset.metadata = result["metadata"]
        dataset.status = "READ_COMPLETE"
        dataset.save()
        
        logger.info(f"Successfully processed dataset {dataset_id}")
        
        # Clean up the temporary file
        try:
            os.remove(file_path)
            logger.info(f"Removed temporary file {file_path}")
        except Exception as e:
            logger.warning(f"Failed to remove temporary file {file_path}: {str(e)}")
        
        return {
            "success": True,
            "dataset_id": str(dataset_id),
            "file_url": result["url"]
        }
    
    except Exception as e:
        logger.error(f"Error processing dataset {dataset_id}: {str(e)}")
        
        # Try to update the dataset status to indicate failure
        try:
            dataset = Dataset.objects.get(object_id=dataset_id)
            dataset.status = "READ_FAILED"
            dataset.save()
        except Exception as inner_e:
            logger.error(f"Failed to update dataset status: {str(inner_e)}")
        
        # Clean up the temporary file
        try:
            os.remove(file_path)
        except:
            pass
        
        return {
            "success": False,
            "dataset_id": str(dataset_id),
            "error": str(e)
        }
