from pydantic import BaseModel

#x=0.141, y=0.07, z=0.361,
#roll=0.553, pitch=1.264, yaw=1.111

class Pose(BaseModel):
    x:float
    y:float
    z:float
    roll:float
    pitch:float
    yaw:float
    class Config:
        orm_mode = True

class Features(BaseModel):
    shape:str
    color:str        
    class Config:
        orm_mode=True

class Conveyor(BaseModel):
    workspace_name:str
    shape:str
    color:str       
    class Config:
        orm_mode=True
