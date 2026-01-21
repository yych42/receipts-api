from pydantic import BaseModel, Field


class ImageDataRequest(BaseModel):
    image: str = Field(
        ...,
        description="A Base64 encoded image string or a URL to an image.",
    )
    hint: str | None = Field(
        None,
        description="A hint to help the model understand the context of the image.",
        max_length=200,
    )
    language: str | None = Field(
        None,
        description="The language of the event. By default, the model will respond in the language of the text in the image.",
    )
