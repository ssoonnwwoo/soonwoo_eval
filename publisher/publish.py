from shotgun_api3 import Shotgun
import os
import sys
import socket
import maya.cmds as cmds

from systempath import SystemPath
from shotgridapi import ShotgridAPI
root_path = SystemPath().get_root_path()
sg = ShotgridAPI().shotgrid_connector()
maya_usd_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../loader"))
sys.path.append(maya_usd_path)

from loader.shotgrid_user_task import TaskInfo, UserInfo, ClickedTask

class PublishManager:
    def __init__(self,clicked_task):
        print(f"여기는 PublishManager : {clicked_task}")
        self.clicked_task = clicked_task
        self.project_id = clicked_task.proj_id
        self.task_id = clicked_task.id
        self.entity_id = clicked_task.entity_id
        self.entity_type = self.get_entity_type(clicked_task.entity_type)
        self.assignee = self.get_assignee()
        self.file_name = ""
        self.file_path = ""
        self.description = ""
        self.thumbnail_path = ""
        self.mov_path = ""

    def __repr__(self):
        return (
            f"PublishManager(\n"
            f"  project_id={self.project_id},\n"
            f"  task_id={self.task_id},\n"
            f"  entity_id={self.entity_id},\n"
            f"  entity_type={self.entity_type},\n"
            f"  assignee={self.assignee},\n"
            f"  file_name={self.file_name},\n"
            f"  file_path={self.file_path},\n"
            f"  description={self.description},\n"
            f"  thumbnail_path={self.thumbnail_path},\n"
            f"  mov_path={self.mov_path}\n"
            f")"
        )

    def get_entity_type(self, entity_type):
        return "Shot" if entity_type == "seq" else "Asset"
    
    # 자신의 내부망 주소 get
    def get_internal_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))  
            internal_ip = s.getsockname()[0]
        except Exception:
            internal_ip = "127.0.0.1"
        finally:
            s.close()
        return internal_ip
    
    # ip로 Shotgrid HumanUser find
    def get_assignee(self):
        internal_ip = self.get_internal_ip()
        last_ip = int(internal_ip.split(".")[-1])
        return sg.find_one("HumanUser", [["sg_ip", "is", last_ip]])
    
    def set_file_path(self,file_path):
        # file_path = "/nas/eval/show/eval/assets/vehicle/bike/model/pub/usd/bike_model.usda"
        self.file_path = file_path

    def set_file_name(self, file_name):
        # file_name = self.file_path.split("/")[-1]
        self.file_name = file_name

    def set_description(self, description):
        self.description = description

    def set_thumbnail_path(self, thumb_path):
        # thumb_path = os.path.abspath(os.path.join(file_path, f"../data/{file_name}"))
        # thumb_path = self.change_ext(thumb_path, ext)
        self.thumbnail_path = thumb_path
    
    def set_mov_path(self, mov_path):
        # mov_path = os.path.abspath(os.path.join(file_path, f"../../data/{file_name}"))
        # mov_path = self.change_ext(mov_path, ext)
        self.mov_path = mov_path

    def change_ext(self, file_path, ext):
        base_name, _ = os.path.splitext(file_path)
        return f"{base_name}.{ext}"
    
    def create_published_file(self):
        published_file_data = {
        "project": {'type': 'Project', 'id': self.project_id}, 
        "code": self.file_name, 
        "task": {'type': 'Task', 'id': self.task_id},
        "entity": {'type': self.entity_type, 'id': self.entity_id},
        "created_by": self.assignee,
        "sg_status_list": "pub",
        "description":self.description,
        "sg_local_path":self.file_path,
        "image" : self.thumbnail_path
        }

        published_file = sg.create("PublishedFile", published_file_data)
        print(f"Published File successfully created!")
        print(published_file)
        return published_file

    def create_versions(self):
        print(f"Try create version")
        version_data = {
            "project" : {'type': 'Project', 'id': self.project_id}, 
            "code" : self.file_name,
            "sg_task" : {'type': 'Task', 'id': self.task_id},
            "entity" : {'type': self.entity_type, 'id': self.entity_id},
            "user" : self.assignee,
            "sg_status_list" : "rev",
            "description" : self.description
        }
        created_version = sg.create("Version", version_data)
        sg.upload("Version", created_version["id"], self.mov_path, field_name="sg_uploaded_movie")
        print(f"Version successfully created")
        print(created_version)
        return created_version
    
    def link_version_to_published_file(self, pub_id, version_id):
        sg.update("PublishedFile", pub_id, {"version":{"type":"Version", "id":version_id}})
        

if __name__ == "__main__":
    sg_url = "https://5thacademy.shotgrid.autodesk.com/"
    script_name = "sy_key"
    api_key = "vkcuovEbxhdoaqp9juqodux^x"

    my_dict = {
        "proj_name" : "eval",
        "proj_id" : 122,
        "id" : 6196,
        "entity_id" : 1255,
        "entity_name" : "AAB_0010",
        "entity_type" : "seq",
        "entity_parent" : "AAB",
        "step": "Light"
        }
    
    # my_dict = {
    #     "proj_name" : "eval",
    #     "proj_id" : 123,
    #     "id" : 6084,
    #     "entity_id" : 1214,
    #     "entity_name" : "AAB_0010",
    #     "entity_type" : "seq",
    #     "entity_parent" : "AAB",
    #     "step": "Light"
    #     }
    my_dict = {
        "proj_name" : "eval",
        "assignee_id" : 112, 
        "proj_id" : 123,
        "id" : 6045,
        "content" : "bike_rig",
        "entity_id" : 1431,
        "entity_name" : "bike",
        "entity_type" : "assets",
        "entity_parent" : "Vehicle",
        "step": "Model"
        }
    clicked_task = ClickedTask(my_dict)
    publish_manager = PublishManager(clicked_task)

    # file_name = "AAB_0010_light_v001.usd"
    # local_path = "/nas/eval/show/eval/seq/AAB/AAB_0010/light/pub/maya/scenes/AAB_0010_light_v001.usd"
    # status = "pub"
    # description = "Final render for shot X" 
    # #thumbnail_path = "/nas/eval/show/eval/seq/AAB/AAB_0010/light/pub/maya/data/AAB_0010_light.jpg" 
    
    file_name = "bike_model_v001.usd"
    local_path = "/nas/eval/show/eval/assets/vehicle/bike/model/pub/maya/scenes/bike_model_v001.usd"
    status = "pub"
    description = "Bike model v001 publish" 
    #thumbnail_path = "/nas/eval/show/eval/assets/vehicle/bike/model/pub/maya/data/bike_model_v001.jpg" 
    
    publish_manager.set_file_name(file_name)
    publish_manager.set_file_path(local_path)
    publish_manager.set_file_name(local_path)
    publish_manager.set_description(description)
    publish_manager.set_thumbnail_path(local_path, "jpg")
    publish_manager.set_mov_path(local_path, "mov")

    created_version = publish_manager.create_versions()
    published_file = publish_manager.create_published_file()
    publish_manager.link_version_to_published_file(published_file["id"], created_version["id"])
