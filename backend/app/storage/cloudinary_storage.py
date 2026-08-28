import os
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader

load_dotenv()

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
)

def upload_pdf(local_file_path: str, public_id: str) -> dict:
    response = cloudinary.uploader.upload(
        local_file_path,
        resource_type="raw",
        public_id=public_id,
        overwrite=True,
    )
    return response

def delete_pdf(public_id: str) -> dict:
    return cloudinary.uploader.destroy(public_id, resource_type="raw")