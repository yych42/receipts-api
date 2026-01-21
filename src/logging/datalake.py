import io
import json
import base64
import hashlib
from src.clients.r2 import get_data_lake_r2
from src.utils.image import determine_format
from src.utils.ensure_ascii import ensure_ascii


def sink_image(encoded_image: str, metadata: dict, path: str):
    r2 = get_data_lake_r2()
    if r2 is None:
        return  # Skip if R2 not configured

    if not encoded_image:
        raise ValueError("Image is empty. Skipping upload.")

    img_format = determine_format(encoded_image)
    hash = hashlib.sha256((encoded_image + json.dumps(metadata)).encode()).hexdigest()
    r2.upload_fileobj(
        io.BytesIO(base64.b64decode(encoded_image)),
        "latent-data-lake",
        f"{path}/{hash}.{img_format}",
        ExtraArgs={
            "Metadata": ensure_ascii(metadata),
            "ContentType": f"image/{img_format}",
        },
    )
