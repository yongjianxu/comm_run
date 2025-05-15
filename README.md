# comm_run
provide the env and cmds to reproduce some communication test

communication type: in the project:
1. ib_write_bw
2. mooncake transfer_engine_bench

Node to node test. run 8 instance simutanously
both GPU and CPU mem supported

BUILD container image

docker build -t nvcr.io/nvidia/pytorch:25.04-py3-comm -f comm .

start etdc metadata server
etcd --listen-client-urls http://10.6.131.1:2379  --advertise-client-urls http://10.6.131.1:12345 &![image](https://github.com/user-attachments/assets/b1e8e6ed-0b73-4875-89eb-21b6d1caf4d1)

