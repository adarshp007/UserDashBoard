from django.shortcuts import render
from django.http import JsonResponse
from utils.backblaze import upload_file_to_b2
from django.views.decorators.csrf import csrf_exempt
# Create your views here.
@csrf_exempt
def upload_view(request):
    if request.method == "POST" and request.FILES.get("file"):
        file = request.FILES["file"]
        # Trim whitespace and replace spaces with underscores
        clean_filename = "_".join(file.name.strip().split())
        file_path = f"/tmp/{clean_filename}"
        # Save file temporarily
        with open(file_path, "wb") as f:
            for chunk in file.chunks():
                f.write(chunk)
        file_url = upload_file_to_b2(file_path, clean_filename)
        return JsonResponse({"message": "File uploaded!", "url": file_url})
    return JsonResponse({"error": "Invalid request"}, status=400)