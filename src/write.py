import subprocess
import logging
import datetime
import sys
import socket
import os
import glob
hostname = socket.gethostname()
# Test config
clients = ['10.6.131.1']
servers = ['10.6.131.2']
# make sure ibdevs and cudevs matches in locality
cudevs = [0,1,2,3,4,5,6,7]
ibdevs = ['mlx5_3','mlx5_2','mlx5_1','mlx5_0','mlx5_5','mlx5_4','mlx5_7','mlx5_6']
ports = [6667,6668,6669,6670,6671,6672,6673,6674]

class WRITE:
    def __init__(self,ibdev, server_ip=None, port=18515, size=65536, iterations=1000, cuda=None):
        """
        Initialize WRITE class with ib_write_bw parameters
        
        Args:
            server_ip (str): IP address of the server
            port (int): Port number (default: 18515)
            size (int): Message size in bytes (default: 65536)
            iterations (int): Number of iterations (default: 1000)
            cuda (int, optional): CUDA device number to use (default: None)
        """
        self.ibdev=ibdev
        self.server_ip = server_ip
        self.port = port
        self.size = size
        self.iterations = iterations
        self.cuda = cuda
        self.logger = logging.getLogger(__name__)
    
    def run(self, **kwargs):
        """
        Run ib_write_bw command in a subprocess
        
        Args:
            **kwargs: Additional arguments to pass to ib_write_bw
        
        Returns:
            subprocess.CompletedProcess: Result of the subprocess execution
        """
        cmd = [
            'ib_write_bw',
            '-d', self.ibdev,
            '-p', str(self.port),
            '-s', str(self.size),
            '-n', str(self.iterations),
            '--report_gbits',
            '-F',
            '-D', '10',
            '-x', '3',
        ]
        
        # Add CUDA device if specified
        if self.cuda is not None:
            cmd.append(f'--use_cuda={self.cuda}')
        
        # Add server_ip if it exists
        if self.server_ip is not None:
            cmd.append(self.server_ip)
        # Add any additional arguments
        for key, value in kwargs.items():
            if isinstance(value, bool):
                if value:
                    cmd.append(f'-{key}')
            else:
                cmd.extend([f'-{key}', str(value)])
        
        try:
            self.logger.info(f"Running command: {' '.join(cmd)}")
            
            # Create a unique filename based on timestamp and device
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"../results/ib_write_bw_{self.ibdev}_{timestamp}.log"
            
            # Open file to capture output
            with open(output_file, 'w') as f:
                f.write(f"Command: {' '.join(cmd)}\n\n")
                f.flush()
                
                # Run the process and redirect output to file
                process = subprocess.Popen(
                    cmd,
                    stdout=f,
                    stderr=f,
                    text=True
                )
                
                self.logger.info(f"Writing output to {output_file}")
                return process

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error running ib_write_bw: {e}")
            raise

def cpu_perftest():
    # Check if hostname is in client or server list
    if hostname in clients: 
        for i in range(len(ibdevs) + 1):
            ibdev = ibdevs[i % len(ibdevs)]  # Alternate between mlx5_0 and mlx5_1
            port = ports[i % len(ports)]      # Alternate between ports
            server = servers[i % len(servers)]
            write = WRITE(ibdev, server_ip=server, port=port)
            write.run()
    elif hostname in servers:
        for i in range(len(ibdevs)):
            ibdev = ibdevs[i % len(ibdevs)]  # Alternate between mlx5_0 and mlx5_1
            port = ports[i % len(ports)]      # Alternate between ports
            write = WRITE(ibdev, port=port)
            write.run() 
    else:
        print(f"Unexpected hostname: {hostname}")
        sys.exit(1)
def gpu_perftest():
    # Check if hostname is in client or server list
    if hostname in clients: 
        for i in range(len(ibdevs) + 1):
            ibdev = ibdevs[i % len(ibdevs)]  # Alternate between mlx5_0 and mlx5_1
            port = ports[i % len(ports)]      # Alternate between ports
            server = servers[i % len(servers)]
            cuda = cudevs[i % len(cudevs)]
            write = WRITE(ibdev, server_ip=server, port=port, cuda=cuda)
            write.run()
    elif hostname in servers:
        for i in range(len(ibdevs)):
            ibdev = ibdevs[i % len(ibdevs)]  # Alternate between mlx5_0 and mlx5_1
            port = ports[i % len(ports)]  
            cuda = cudevs[i % len(cudevs)]
            write = WRITE(ibdev, port=port, cuda=cuda)
            write.run() 
    else:
        print(f"Unexpected hostname: {hostname}")
        sys.exit(1)
def report_write():
    # Get all log files in results directory
    log_files = glob.glob('results/*.log')
    
    for file_path in log_files:
        print(f"\nFile: {file_path}")
        print("-" * 50)
        
        try:
            with open(file_path, 'r') as f:
                # Read all lines and get last 5
                lines = f.readlines()
                last_5_lines = lines[-5:] if len(lines) >= 5 else lines
                
                # Print last 5 lines
                for line in last_5_lines:
                    print(line.rstrip())
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")

gpu_perftest()
