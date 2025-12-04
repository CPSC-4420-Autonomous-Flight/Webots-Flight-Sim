# Autonomous Flight Project

This project demonstrates autonomous quadcopter navigation through simulated environments using a locally hosted Vision Language Model (VLM). The system can avoid stationary and moving obstacles while choosing optimal paths between coordinates.

## Demo

🎥 [Watch the VLM Drone Demo](https://www.youtube.com/watch?v=FZS9JRm_2Zc)

## Models

### Ollama Setup

1. **Install Ollama** for your machine: https://ollama.com/download/

2. **Pull the LLaVA model:**
   ```bash
   ollama pull llava
   ```

3. **Run LLaVA:**
   ```bash
   ollama run llava
   ```

4. **Start the VLM server:**
   ```bash
   python Ollama_vlm_server.py
   ```

### Alternative: vlm_server.py Setup

1. **Create a new folder and install dependencies:**
   ```bash
   pip install torch transformers pillow fastapi uvicorn accelerate
   ```

2. **Place the `vlm_server.py` file** in the folder you just created

3. **Install additional dependency:**
   ```bash
   pip install python-multipart
   ```

4. **Start the server:**
   ```bash
   uvicorn vlm_server:app --host 0.0.0.0 --port 8000
   ```
   > **Note:** Run this command from the same folder containing `vlm_server.py`
   
   When running successfully, you should see:
   
   <img width="508" height="91" alt="Server running confirmation" src="https://github.com/user-attachments/assets/ed44b773-dfff-422c-b7a3-2df1b21d05a6" />
   
   This confirms the VLM is running locally.

5. **Access the FastAPI interface:**
   - Navigate to `http://localhost:8000/docs` in your browser
   - You can upload JPG files and receive responses

#### Example Input/Output

**Input:**

![Trash can](https://github.com/user-attachments/assets/8daae350-04cf-4022-9010-51b38dfbee3a)

**Output:**
```json
{
  "caption": "A garbage can full of trash.",
  "decision": "safe"
}
```

## Environments

All simulated environments are taken from Webots prebuilt environments.

### Accessing Sample Worlds

1. Navigate to: **File > Open Sample World > Vehicles**
2. Choose any environment to simulate a realistic outdoor environment for drone maneuvering

### Python Configuration

Ensure your Webots environment is connected to your Python installation:

1. Go to **Tools > Preferences > Python command**
2. Paste your Python path
3. To find your Python path:
   - Open Command Prompt
   - Type `where python`
   - Copy the first path returned

## Quadcopters

This project uses the **Mavic2PRO** drone model.

### Adding a New Mavic2Pro

1. Click the **"+" sign** above the scene editor
2. Search for `Mavic2Pro`
3. Select **Mavic2Pro**
4. Move the drone to your desired location using the green and red adjustment lines

## Controllers

All controllers in this project are designed for the Mavic2Pro quadcopter and written in Python.

### Creating a New Controller

1. **File > New > New Robot Controller**
2. Select language (Python)
3. Name your controller
4. Click **Finish**

### Attaching a Controller to a Drone

**Method 1:**
1. Open the scene editor
2. Select the drone
3. Click on the controller field
4. Choose your controller from the dropdown list
5. Ensure the controller file is saved in the correct controllers path

**Method 2 (Edit Existing):**
1. Open the scene editor
2. Select the drone
3. Click on the controller field and select **Edit**
4. This opens the controller file where you can edit or paste code
5. Save the file

## Todo

- [ ] Integrate additional sensors (Lidar, infrared) into simulation
- [ ] Refine VLM prompts to improve quadcopter movement responsiveness
- [ ] Build custom obstacle course environment optimized for quadcopter navigation
- [ ] Improve response smoothness and flight stability

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.
