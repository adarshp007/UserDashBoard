from django.shortcuts import render
from django.http import JsonResponse
from utils.backblaze import upload_file_to_b2
# Create your views here.

def upload_view(request):
    if request.method == "POST" and request.FILES.get("file"):
        file = request.FILES["file"]
    
        file_path = f"/tmp/{file.name}"
        # Save file temporarily
        with open(file_path, "wb") as f:
            for chunk in file.chunks():
                f.write(chunk)
        file_url = upload_file_to_b2(file_path, file.name)
        return JsonResponse({"message": "File uploaded!", "url": file_url})
    return JsonResponse({"error": "Invalid request"}, status=400)