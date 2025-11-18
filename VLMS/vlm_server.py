from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import ollama
import io

app = FastAPI()

SYSTEM_PROMPT = """
You are a drone flight controller. You only output single commands.
Analyze the image. 
If the path ahead is clear, say "safe".
If there is an obstacle directly ahead, say "unsafe_forward".
If there is an obstacle ahead but the left is clear, say "turn_left".
If there is an obstacle ahead but the right is clear, say "turn_right".
Do not say anything else. Do not explain.
"""

@app.post("/vlm")
async def vlm_endpoint(file: UploadFile = File(...)):
    # Read the image bytes sent by the drone
    image_bytes = await file.read()

    try:
        # Send to Ollama (Local AI)
        response = ollama.chat(
            model='llava',
            messages=[{
                'role': 'user',
                'content': SYSTEM_PROMPT,
                'images': [image_bytes]
            }]
        )

        # Extract the text
        decision_text = response['message']['content'].strip().lower()
        
        # Clean up the output (LLMs sometimes add punctuation)
        decision = "safe" # Default fallback
        
        if "turn_left" in decision_text:
            decision = "turn_left"
        elif "turn_right" in decision_text:
            decision = "turn_right"
        elif "unsafe" in decision_text or "stop" in decision_text:
            decision = "unsafe_forward"
        elif "safe" in decision_text:
            decision = "safe"

        print(f"AI saw: {decision_text} -> Command: {decision}")
        
        return JSONResponse({"caption": decision_text, "decision": decision})

    except Exception as e:
        print(f"Error: {e}")
        return JSONResponse({"decision": "error"})

if __name__ == "__main__":
    import uvicorn
    print("Starting VLM Server on port 8000...")
    uvicorn.run(app, host="127.0.0.1", port=8000)