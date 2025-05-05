#!/bin/bash
# Simple script to restart the Celery worker container
docker-compose restart celery
echo "Celery worker restarted"
