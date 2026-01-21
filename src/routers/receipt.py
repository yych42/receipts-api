from fastapi import APIRouter, BackgroundTasks
from src.utils.openai_image import ask_openai_with_image
from src.utils.download_image import download_image_from_url
from src.logging import datalake
import base64
from pydantic import BaseModel, Field
from src.clients.ratelimit import ratelimit
from datetime import datetime
from src.models.image_data import ImageDataRequest

router = APIRouter(
    prefix="/image/extract",
    tags=["Image"],
)


class ReceiptItemDiscount(BaseModel):
    name: str
    discount_amount: float = Field(
        ..., description="The amount of the discount; this should be negative."
    )


class ReceiptItem(BaseModel):
    name: str
    unit_price: float
    unit_label: str
    quantity: float
    total_price: float
    category: str | None
    discount: ReceiptItemDiscount | None


class Receipt(BaseModel):
    merchant: str
    items: list[ReceiptItem]
    total: float
    date: str
    time: str
    currency: str
    tax: float = Field(
        ...,
        description="The tax amount for the receipt.",
    )


@router.post("/receipt", response_model=Receipt)
async def parse_receipt_from_image(
    request: ImageDataRequest,
    background_tasks: BackgroundTasks,
) -> Receipt:
    ratelimit("/image/extract/receipt")  # Default: 100 requests per hour

    if request.image.startswith("http"):
        request.image = base64.b64encode(download_image_from_url(request.image)).decode(
            "utf-8"
        )

    if not request.hint:
        request.hint = ""

    response: Receipt = ask_openai_with_image(
        request.image,
        f"Today is {datetime.now().strftime('%B %-d, %Y')}." + request.hint,
        Receipt,
        low_quality_mode=False,
        system_prompt=(
            f"Fill the receipt information in this language: {request.language}."
            if request.language
            else "Fill the receipt information in the language of the text in the image."
            + "All prices, totals, amounts should be signed if they are negative. Note that certain items may also have a negative sign, such as gift cards or recycle credits (e.g. Pant in swedish)."
        ),
    )

    background_tasks.add_task(
        datalake.sink_image,
        request.image,
        {
            "datetime": datetime.now().isoformat(),
            "request": {
                "hint": request.hint or "",
                "language": request.language or "auto",
            },
            "response": response.model_dump(),
        },
        "image/extract/receipt",
    )

    return response
