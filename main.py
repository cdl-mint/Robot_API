from fastapi import FastAPI,HTTPException, status
from model import Pose,Features,Conveyor
from session import settings
from typing import List
from pyniryo import *

tags_metadata = [
    {
         "name": "Robots",
        "description": "Calibration on robots",
    },
    {
"name":"Conveyor",
"description": "Operation on conveyor",
    },
    {
       "name":"Gripper",
"description": "Operation on gripper", 
    }
]
app=FastAPI(title=settings.PROJECT_NAME,version=settings.PROJECT_VERSION, openapi_tags=tags_metadata)

#connect to robot ip 192.168.0.108
robot_ip_address = "192.168.0.108"
robot=NiryoRobot(robot_ip_address)
conveyor_id = robot.set_conveyor()
workspace_name = "default_workspace"
robot.update_tool()
# -- Can change these variables
grid_dimension = (3, 3)
conveyor_id = ConveyorID.ID_1
gripper_speed = 400
robot.calibrate_auto()

# -- Should Change these variables
observation_pose = [0.721, 0.347, -0.785,0.138, -0.724, -0.007]

center_conditioning_pose = PoseObject(
    x=0.232, y=-0.022, z=0.07,
    roll=-2.906, pitch=1.428, yaw=-2.831
)

def pick_n_place(robot):
    max_catch_count = 6
    shape_expected = ObjectShape.SQUARE
    color_expected = ObjectColor.RED
    catch_count = 0
    while catch_count < max_catch_count:
        # Turning conveyor on
        robot.run_conveyor(conveyor_id)
        # Moving to observation pose
       
        robot.move_joints(observation_pose)
        # Check if object is in the workspace
        obj_found, pos_array, shape, color = robot.detect_object(workspace_name,
                                                                       shape=shape_expected,
                                                                       color=color_expected)
        if not obj_found:
            robot.wait(0.5)  # Wait to let the conveyor turn a bit
            continue
        # Stopping conveyor
        robot.stop_conveyor(conveyor_id)
        # Making a vision pick
        obj_found, shape, colo = robot.vision_pick(workspace_name,
                                                         shape=shape_expected,
                                                         color=color_expected)
        if not obj_found:  # If visual pick did not work
            continue
        # Calculating offset relative to conditioning center position
        offset_x = catch_count % grid_dimension[0] - grid_dimension[0] // 2
        offset_y = (catch_count // grid_dimension[1]) % 3 - grid_dimension[1] // 2
        place_pose = center_conditioning_pose.copy_with_offsets(0.05 * offset_x, 0.05 * offset_y)
        # Going to place
        robot.place_from_pose(center_conditioning_pose)
        catch_count += 1
    # Stopping conveyor
    robot.stop_conveyor(conveyor_id)

    # Going to initial Observation pose
    robot.move_pose(observation_pose)

#check if robot needs calibration 
@app.get("/Robots/Calibration",tags=["Robots"], status_code=status.HTTP_200_OK)
def need_calibration():
 robot.calibrate_auto()
 result =robot.need_calibration()
 return result

#send calliberation to db 
@app.post("/Robots/Move_Position",status_code=201, tags=["Robots"])
def send_move_pose():
    movejoints=robot.move_joints(-0.5, -0.6, 0.0, 0.3, 0.5, 0.0)
    ObservationPose=PoseObject(x=0.141, y=0.07, z=0.361,roll=0.553, pitch=1.264, yaw=1.111)
    movePose=robot.move_pose(ObservationPose)
    print(movejoints)
    return movejoints
   

#get calliberation from db
@app.get("/Robots/CurrentPosition",tags=["Robots"], status_code=status.HTTP_200_OK)
def get_current_position():
    pose=robot.get_pose()
    return pose

@app.post("/Robots/Close_Connection",status_code=status.HTTP_200_OK, tags=["Robots"])
def close_connection():
    close=robot.close_connection() 
    return close    
       
# Activating connection with Conveyor Belt
@app.post("/Robots/Activate_Conveyor",status_code=status.HTTP_200_OK, tags=["Conveyor"])
def Activate_Conveyor_Belt():
    # Running the Conveyor Belt at 50% of its maximum speed, in forward direction
    robot.run_conveyor(conveyor_id, speed=50, direction=ConveyorDirection.FORWARD)
    return conveyor_id

# Stopping robot's motor
@app.post("/Robots/De_Activate_Conveyor",status_code=status.HTTP_200_OK, tags=["Conveyor"])
def Deactivate_Conveyor():
    robot.stop_conveyor(conveyor_id)
    # Deactivating connexion with the Conveyor Belt
    robot.unset_conveyor(conveyor_id) 
    return conveyor_id                                                   

#pick and place with robot
@app.post("/Robots/Pick_Place_Pump",status_code=status.HTTP_200_OK, tags=["Conveyor"])
def Gripper(): 
 tool_Id=robot.update_tool()
 pick_n_place(robot)
# Ending
 robot.go_to_sleep()

@app.post("/Robots/Gripper",status_code=status.HTTP_200_OK, tags=["Gripper"])
def gripper_pick_and_place():
    robot.calibrate_auto()
    robot.update_tool()
    robot.open_gripper(gripper_speed)
    pick_pose=(0.150,.1270,0.152,-0.0030,0.7210,0.704)
    place_pose=(0.246,0,0.268,-0.0011,1.5030,0.001)
    robot.pick_and_place(pick_pose, place_pose)
    # Pick
    robot.pick_from_pose(pick_pose)
    # Place
    robot.place_from_pose(place_pose)
    robot.close_gripper(gripper_speed)
    
@app.post("/Robots/Gripper_Open",status_code=status.HTTP_200_OK, tags=["Gripper"])
def gripper_open():
    robot.open_gripper(gripper_speed)
    robot.go_to_sleep()

@app.post("/Robots/Gripper_Close",status_code=status.HTTP_200_OK, tags=["Gripper"])
def gripper_close():
    robot.close_gripper(gripper_speed)
    robot.go_to_sleep()
    