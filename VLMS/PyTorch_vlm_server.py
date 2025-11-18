from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from PIL import Image
import io
import torch
from transformers import AutoProcessor, AutoModelForVision2Seq

app = FastAPI()

# Load your VLM model here (LLaVA, Qwen-VL, etc.)
MODEL_NAME = "llava-hf/llava-1.5-7b-hf"

print("Loading VLM model...")
processor = AutoProcessor.from_pretrained(MODEL_NAME)
model = AutoModelForVision2Seq.from_pretrained(
    MODEL_NAME,
    torch_dtype=torch.float16,
    device_map="auto"
)
print("VLM Ready.")

def caption_to_decision(caption: str):
    caption = caption.lower()

    if "wall" in caption or "obstacle" in caption or "blocked" in caption:
        return "unsafe_forward"
    if "clear left" in caption or ("left" in caption and "clear" in caption):
        return "turn_left"
    if "clear right" in caption or ("right" in caption and "clear" in caption):
        return "turn_right"

    return "safe"

@app.post("/vlm")
async def vlm_endpoint(file: UploadFile = File(...)):
    image_bytes = await file.read()
    image = Image.open(io.BytesIO(image_bytes))

    inputs = processor(
        images=image,
        text="Describe obstacles ahead in 1 short sentence.",
        return_tensors="pt"
    ).to(model.device)

    output = model.generate(**inputs, max_length=40)
    caption = processor.decode(output[0], skip_special_tokens=True)

    decision = caption_to_decision(caption)

    return JSONResponse({"caption": caption, "decision": decision})
