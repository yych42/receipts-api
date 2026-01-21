from PIL import Image
import io
import base64


def determine_format(image: str):
    try:
        img = Image.open(io.BytesIO(base64.b64decode(image)))
        img.verify()
        img_format = img.format.lower()
        if img_format == "mpo":
            img_format = "jpeg"
        if img_format not in ["jpeg", "png"]:
            raise ValueError(
                "Invalid image format. Only JPEG and PNG are supported. Received: "
                + img_format
            )
    except Exception as e:
        print("Error processing the image:", e)
        return {"error": "Error processing the image."}
    else:
        return img_format
