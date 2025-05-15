import os
import subprocess

class mycontainer:
    def __init__(self):
        image = "nvcr.io/nvidia/pytorch:25.04-py3-comm"
        u = subprocess.run(["id", "-u"], capture_output=True, text=True).stdout.replace("\n","")
        g = subprocess.run(["id", "-g"], capture_output=True, text=True).stdout.replace("\n","")
        cmd = "docker run --name mytest --cap-add=SYS_NICE --cap-add=IPC_LOCK --cap-add=SYS_ADMIN --gpus all --ulimit memlock=-1 --ulimit stack=2000000000 --init -ti -p 12345:12345 -p 2379:2379 --shm-size 32g --network=host -v /usr/src:/usr/src -v /lib/modules:/lib/modules --device=/dev/infiniband/ " + " " + image + " " + "bash"
        print(cmd) 
        os.system(cmd) 

        
project = mycontainer()
