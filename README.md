# Clover Drone Web Server

Web server for controlling COEX Clover drone with character-based interactions.

## Prerequisites

- COEX Clover drone with ROS setup
- Python 3.7 or higher
- ROS environment properly configured

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure the drone's ROS environment is sourced:
```bash
source /opt/ros/noetic/setup.bash  # Adjust for your ROS version
source ~/catkin_ws/devel/setup.bash
```

## Running the Server

1. Start the server:
```bash
python3 drone/tw_drone_webserver.py
```

The server will run on `http://localhost:3001`.

## API Endpoints

### Takeoff
```http
POST /api/drone/takeoff
```
Initiates drone takeoff to 1.5 meters height.

### Turn
```http
POST /api/drone/turn?character={character}
```
Turns drone to show specific character side.

Available characters:
- `business` - Front
- `creative` - Back
- `mystery` - Left side
- `innovation` - Right side
- `default` - Front

### Audio (Placeholder)
```http
POST /api/drone/audio
```
Placeholder for future audio streaming implementation.

## Safety Notes

- Always ensure proper safety measures when operating the drone
- Keep clear space around the drone during operation
- Have a physical remote control ready for manual override if needed