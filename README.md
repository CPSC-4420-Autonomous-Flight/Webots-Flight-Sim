MAVIC2CONTROLLER.PY 
- Need to install numpy at the path you have installed your python.exe at
- Use Mavic 2 Pro drone with this controller

PIDcontroller folder
- To use, drag and drop to .\WebotsProjectFolder\controllers

Vlm_server.py -HOW TO USE
1. Create new folder and run "pip install torch transformers pillow fastapi uvicorn accelerate" in it
2. put vlm_server.py file in the same folder you just created
3. run "pip install python-multipart" in same folder
4. Use the following command in the terminal "uvicorn vlm_server:app --host 0.0.0.0 --port 8000" to start the server. (Be sure that you are running this command while in the same folder as your vlm_server.py file
    You should see the following in your terminal <img width="508" height="91" alt="image" src="https://github.com/user-attachments/assets/ed44b773-dfff-422c-b7a3-2df1b21d05a6" />
    This means that the VLM is running locally
5. Run "http://localhost:8000/docs" in your URL to access the FastAPI
6. Here you can upload JPG files and get responses back

EXAMPLE INPUT/OUTPUT
    When inputing
    
 ![Trash can](https://github.com/user-attachments/assets/8daae350-04cf-4022-9010-51b38dfbee3a) 
  
    The respoonse body should be 
  
    "{
    "caption": "A garbage can full of trash.",
    "decision": "safe"}"

  
