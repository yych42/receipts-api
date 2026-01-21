from fastapi import FastAPI
from src.routers.receipt import router as receipt_router

app = FastAPI(
    title="Receipts API",
    description="A lightweight API for extracting structured data from receipt images",
    version="1.0.0",
)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/")
async def root():
    return {"message": "Receipts API", "docs": "/docs"}


app.include_router(receipt_router)
