"""
Drone Controller: Hover-and-Think with VLM Integration v1
"""
from controller import Robot, Keyboard
import sys
import threading
import requests
import time
import io

try:
    import numpy as np
    import cv2 # Used for image encoding
except ImportError:
    sys.exit("Warning: 'numpy' or 'cv2' module not found. Please install them.")

def clamp(value, value_min, value_max):
    return min(max(value, value_min), value_max)

class Mavic(Robot):
    
    # API Configuration
    VLM_URL = "http://127.0.0.1:8000/vlm" 

    # 1. TRIM 
    TRIM_PITCH = 0.1   
    TRIM_ROLL = 0.0    

    # 2. Physics
    K_VERTICAL_THRUST = 68.5  
    K_VERTICAL_OFFSET = 0.6 
    
    # 3. PID Gains
    K_VERTICAL_P = 3.0        
    K_VERTICAL_D = 2.0        
    K_YAW_P = 2.0             
    K_ROLL_P = 50.0           
    K_ROLL_I = 0.01           
    K_PITCH_P = 30.0          
    K_PITCH_I = 0.01          

    # 4. Limits
    MAX_YAW_DISTURBANCE = 0.8
    MAX_PITCH_DISTURBANCE = -1
    INTEGRAL_LIMIT = 1.0      
    
    # 5. Thresholds & Settings
    TARGET_ALTITUDE = 1.0
    STABLE_THRESHOLD = 0.05   
    
    MOVE_DURATION = 1.0       
    MOVE_SPEED = 0.5          
    TURN_ANGLE = 30.0     
    LANDING_SPEED = 0.2

    def __init__(self):
        Robot.__init__(self)
        self.time_step = int(self.getBasicTimeStep())

        # Sensors
        self.imu = self.getDevice("inertial unit")
        self.imu.enable(self.time_step)
        self.gps = self.getDevice("gps")
        self.gps.enable(self.time_step)
        self.gyro = self.getDevice("gyro")
        self.gyro.enable(self.time_step)
        self.camera = self.getDevice("camera")
        self.camera.enable(self.time_step)
        self.keyboard = self.getKeyboard()
        self.keyboard.enable(self.time_step)

        # Motors
        self.motors = [
            self.getDevice("front left propeller"),
            self.getDevice("front right propeller"),
            self.getDevice("rear left propeller"),
            self.getDevice("rear right propeller")
        ]
        for motor in self.motors:
            motor.setPosition(float('inf'))
            motor.setVelocity(1)

        self.camera_pitch_motor = self.getDevice("camera pitch")
        self.camera_pitch_motor.setPosition(0.0)

        # State
        self.target_yaw = 0.0
        self.roll_integral = 0.0
        self.pitch_integral = 0.0
        self.prev_pos = [0, 0, 0] 
        
        # Logic
        self.action_start_time = 0.0
        self.action_initialized = False
        self.last_key = 0
        
        # VLM Threading Variables
        self.vlm_image_data = None      # Stores the image to send
        self.vlm_result = None          # Stores the decision from server
        self.is_thinking = False        # Flag to check if thread is busy
        
        # Start the VLM Background Thread
        self.vlm_thread = threading.Thread(target=self.vlm_worker)
        self.vlm_thread.daemon = True
        self.vlm_thread.start()

    def vlm_worker(self):
        """Background thread that sends images to FastAPI."""
        while True:
            # Wait until the main loop provides an image
            if self.vlm_image_data is not None:
                try:
                    print(f"[VLM] Sending request to {self.VLM_URL}...")
                    
                    # Send POST request
                    files = {'file': ('drone_view.jpg', self.vlm_image_data, 'image/jpeg')}
                    response = requests.post(self.VLM_URL, files=files, timeout=30)
                    
                    if response.status_code == 200:
                        data = response.json()
                        caption = data.get("caption", "")
                        decision = data.get("decision", "safe")
                        print(f"[VLM] Caption: '{caption}' -> Decision: {decision}")
                        self.vlm_result = decision
                    else:
                        print(f"[VLM] Error: Server returned {response.status_code}")
                        self.vlm_result = "error"

                except Exception as e:
                    print(f"[VLM] Connection Error: {e}")
                    self.vlm_result = "error"
                
                # Reset image data to indicate we are done processing
                self.vlm_image_data = None
            
            # Sleep to prevent CPU hogging
            time.sleep(0.1)

    def run(self):
        state = "TAKEOFF"
        print("--- System Start ---")

        # Calibration
        while self.step(self.time_step) != -1:
            _, _, yaw = self.imu.getRollPitchYaw()
            self.target_yaw = yaw
            self.prev_pos = self.gps.getValues()
            print(f"Calibrated. Initial Yaw: {np.rad2deg(yaw):.1f}")
            break

        # Main Loop
        while self.step(self.time_step) != -1:
            dt = self.time_step / 1000.0
            current_time = self.getTime()
            
            # Get Data
            roll, pitch, yaw = self.imu.getRollPitchYaw()
            x, y, altitude = self.gps.getValues()
            roll_vel, pitch_vel, _ = self.gyro.getValues()
            
            # Velocity Calculation
            current_pos = [x, y, altitude]
            vx = (current_pos[0] - self.prev_pos[0]) / dt
            vy = (current_pos[1] - self.prev_pos[1]) / dt
            vz = (current_pos[2] - self.prev_pos[2]) / dt
            self.prev_pos = current_pos
            
            h_speed = np.sqrt(vx**2 + vy**2)

            # Reset Manual Inputs
            pitch_input = self.TRIM_PITCH
            
            # States:

            if state == "TAKEOFF":
                if not self.action_initialized:
                    print("Taking off...")
                    self.action_initialized = True
                
                if altitude > self.TARGET_ALTITUDE - 0.05 and abs(vz) < 0.1:
                    print("Altitude Reached. Stabilizing...")
                    state = "HOVER"
                    self.action_initialized = False

            elif state == "HOVER":
                # Wait for absolute stability
                if h_speed < self.STABLE_THRESHOLD:
                    if not self.is_thinking:
                        print("[THINK] Stabilized. Capturing image...")
                        
                        # Capture Image
                        raw_img = self.camera.getImage()
                        if raw_img:
                            # Convert raw bytes to Numpy 
                            img_arr = np.frombuffer(raw_img, np.uint8).reshape((self.camera.getHeight(), self.camera.getWidth(), 4))
                            # Encode to JPEG for API
                            _, encoded_img = cv2.imencode('.jpg', img_arr)
                            
                            # Pass data to the Thread
                            self.vlm_image_data = encoded_img.tobytes()
                            self.is_thinking = True
                            state = "THINKING"
            
            elif state == "THINKING":
                # While thinking, we just HOVER. 
                # The thread is running in the background.
                # We check if the thread has deposited a result in self.vlm_result
                
                if self.vlm_result is not None:
                    decision = self.vlm_result
                    self.vlm_result = None 
                    self.is_thinking = False 
                    
                    # Map VLM Decision to Drone Action
                    if decision == "safe":
                        print("[ACT] Path Clear -> Moving Forward")
                        self.last_key = ord('W')
                        state = "ACTION"
                    elif decision == "turn_left":
                        print("[ACT] Obstacle -> Turning Left")
                        self.last_key = ord('A')
                        state = "ACTION"
                    elif decision == "turn_right":
                        print("[ACT] Obstacle -> Turning Right")
                        self.last_key = ord('D')
                        state = "ACTION"
                    elif decision == "unsafe_forward":
                        print("[ACT] UNSAFE -> Turning Right to avoid")
                        self.last_key = ord('D')
                        state = "ACTION"
                    elif decision == "error":
                        print("[ACT] Server Error -> Hovering")
                        state = "HOVER"
                    else:
                        state = "HOVER"
                    
                    self.action_initialized = False

            elif state == "ACTION":
                if not self.action_initialized:
                    self.action_start_time = current_time
                    self.action_initialized = True
                    
                    if self.last_key == ord('A'):
                        self.target_yaw += np.deg2rad(self.TURN_ANGLE)
                    elif self.last_key == ord('D'):
                        self.target_yaw -= np.deg2rad(self.TURN_ANGLE)
                    
                    self.target_yaw = (self.target_yaw + np.pi) % (2 * np.pi) - np.pi

                move_complete = False
                
                if self.last_key == ord('W'):
                    pitch_input = self.TRIM_PITCH - self.MOVE_SPEED
                    if current_time - self.action_start_time > self.MOVE_DURATION:
                        move_complete = True
                
                yaw_error = abs(self.target_yaw - yaw)
                if yaw_error > np.pi: yaw_error = 2*np.pi - yaw_error
                
                turn_complete = (self.last_key in [ord('A'), ord('D')]) and (yaw_error < 0.05)

                if move_complete or turn_complete:
                    print("Action Done. Waiting for stability...")
                    state = "HOVER"
                    self.action_initialized = False

            elif state == "LAND":
                self.TARGET_ALTITUDE -= self.LANDING_SPEED * dt
                if self.TARGET_ALTITUDE < -0.5:
                    self.TARGET_ALTITUDE = -0.5
                
                if altitude < 0.1:
                    print("Landed. Engines off.")
                    self.motors[0].setVelocity(0)
                    self.motors[1].setVelocity(0)
                    self.motors[2].setVelocity(0)
                    self.motors[3].setVelocity(0)
                    break 
            
            # Emergency Manual Landing Override (Works in any state)
            key = self.keyboard.getKey()
            if key in [ord('L'), ord('l')]:
                state = "LAND"

            # PID CONTROL 

            self.roll_integral += roll * dt
            self.pitch_integral += pitch * dt
            self.roll_integral = clamp(self.roll_integral, -self.INTEGRAL_LIMIT, self.INTEGRAL_LIMIT)
            self.pitch_integral = clamp(self.pitch_integral, -self.INTEGRAL_LIMIT, self.INTEGRAL_LIMIT)

            roll_level = (self.K_ROLL_P * roll) + (self.K_ROLL_I * self.roll_integral) + roll_vel
            pitch_level = (self.K_PITCH_P * pitch) + (self.K_PITCH_I * self.pitch_integral) + pitch_vel
            
            r_in = roll_level
            p_in = pitch_level + pitch_input 

            yaw_err = self.target_yaw - yaw
            if yaw_err > np.pi: yaw_err -= 2*np.pi
            if yaw_err < -np.pi: yaw_err += 2*np.pi
            y_in = clamp(self.K_YAW_P * yaw_err, -self.MAX_YAW_DISTURBANCE, self.MAX_YAW_DISTURBANCE)

            alt_err = self.TARGET_ALTITUDE - altitude + self.K_VERTICAL_OFFSET
            p_term = self.K_VERTICAL_P * clamp(alt_err, -1.0, 1.0)
            d_term = self.K_VERTICAL_D * vz
            v_in = p_term - d_term

            m1 = self.K_VERTICAL_THRUST + v_in - y_in + p_in - r_in
            m2 = self.K_VERTICAL_THRUST + v_in + y_in + p_in + r_in
            m3 = self.K_VERTICAL_THRUST + v_in + y_in - p_in - r_in
            m4 = self.K_VERTICAL_THRUST + v_in - y_in - p_in + r_in

            self.motors[0].setVelocity(m1)
            self.motors[1].setVelocity(-m2)
            self.motors[2].setVelocity(-m3)
            self.motors[3].setVelocity(m4)

robot = Mavic()
robot.run()