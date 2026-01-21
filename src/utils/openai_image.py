from src.clients.openai_client import openai


def ask_openai_with_image(
    base64_image,
    instruction,
    response_format,
    low_quality_mode=True,
    system_prompt=None,
):
    instruction = instruction.strip()
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": instruction,
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}",
                        "detail": "low" if low_quality_mode else "high",
                    },
                },
            ],
        }
    ]

    if system_prompt:
        messages.insert(
            0,
            {
                "role": "system",
                "content": f"{system_prompt}",
            },
        )

    completion = openai.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06",
        messages=messages,
        response_format=response_format,
    )

    message = completion.choices[0].message

    if message.parsed:
        return message.parsed
    else:
        return message.refusal
