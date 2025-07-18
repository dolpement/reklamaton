#!/usr/bin/env python3

import rospy
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from enum import Enum
from clover import srv
from std_srvs.srv import Trigger
import math

# Initialize ROS node
rospy.init_node('drone_web_server')

# Initialize FastAPI
app = FastAPI(title="Clover Drone Control API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define character orientations (in degrees)
class Character(str, Enum):
    BUSINESS = "business"     # Front (0 degrees)
    CREATIVE = "creative"     # Back (180 degrees)
    MYSTERY = "mystery"       # Left (90 degrees)
    INNOVATION = "innovation" # Right (-90 degrees)
    DEFAULT = "default"       # Front (0 degrees)

# Initialize ROS services
get_telemetry = rospy.ServiceProxy('get_telemetry', srv.GetTelemetry)
navigate = rospy.ServiceProxy('navigate', srv.Navigate)
set_position = rospy.ServiceProxy('set_position', srv.SetPosition)
set_velocity = rospy.ServiceProxy('set_velocity', srv.SetVelocity)
land = rospy.ServiceProxy('land', Trigger)

def wait_for_telemetry():
    """Wait for telemetry to become available"""
    rospy.wait_for_service('get_telemetry')
    return get_telemetry(frame_id='map')

def get_character_yaw(character: Character) -> float:
    """Convert character to yaw angle in radians"""
    yaw_degrees = {
        Character.BUSINESS: 0,      # Front
        Character.CREATIVE: 180,    # Back
        Character.MYSTERY: 90,      # Left
        Character.INNOVATION: -90,  # Right
        Character.DEFAULT: 0,       # Front
    }
    return math.radians(yaw_degrees[character])

@app.post("/api/drone/takeoff")
async def takeoff():
    """Handle drone takeoff command"""
    try:
        # Wait for telemetry
        telemetry = wait_for_telemetry()
        
        # Тут норм по body взлетать?
        navigate(x=0, y=0, z=0.5, frame_id='body', auto_arm=True)
        
        return {
            "status": "success",
            "message": "Drone takeoff initiated."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/drone/turn")
async def turn(character: Character):
    """Handle drone turning based on character"""
    try:
        # Get desired yaw for the character
        target_yaw = get_character_yaw(character)
        
        # Set position with new yaw while maintaining current position
        telemetry = get_telemetry(frame_id='map')
        # ГЕОРГИЙ!!!!!!!, не знаю, что лучше тут использоать, set_position или navigate
        set_position(
            x=telemetry.x,
            y=telemetry.y,
            z=telemetry.z,
            yaw=target_yaw,
            frame_id='map'
        )
        
        return {
            "status": "success",
            "message": f"Drone behavior adjusted to {character} character."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Placeholder for future audio streaming endpoint
@app.post("/api/drone/audio")
async def handle_audio():
    """
    Placeholder for handling audio stream and LED visualization
    This will be implemented later when the web application audio functionality is ready
    """
    return {
        "status": "success",
        "message": "Audio stream placeholder - to be implemented"
    }

if __name__ == "__main__":
    try:
        # Run the FastAPI server
        uvicorn.run(app, host="0.0.0.0", port=3001)
    except KeyboardInterrupt:
        # Attempt to land the drone if the server is interrupted
        try:
            land()
        except:
            pass
