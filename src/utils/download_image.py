from fastapi import HTTPException
import requests
import io
from PIL import Image


def download_image_from_url(url: str) -> bytes:
    try:
        response = requests.get(url)
        response.raise_for_status()
        image_data = response.content
        image = Image.open(io.BytesIO(image_data))
        image.verify()
        return image_data
    except (requests.exceptions.RequestException, IOError, ValueError) as e:
        raise HTTPException(
            status_code=400, detail="Failed to download or validate the image."
        ) from e
