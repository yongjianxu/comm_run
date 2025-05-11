import logging
import time
import socket
from typing import Optional, List
import sys
import subprocess
import signal

# Configuration constants
DEFAULT_BLOCK_SIZE = 512 * 8192
DEFAULT_BATCH_SIZES = [100]
DEFAULT_BUFFER_SIZE = 10 * 1024 * 1024 * 1024
ETCD_PORT = 2379

# Global configuration
target_host = ['H20-GPU-01']
client_host = ['H20-GPU-02']
gpus = [0, 1, 2, 3, 4, 5, 6, 7]  # Default list of GPUs
devs = ['mlx5_3','mlx5_2','mlx5_1','mlx5_0','mlx5_5','mlx5_4','mlx5_7','mlx5_6']
ports = [12345,12346,12347,12348,12349,12350,12351,12352]


# Network configuration
local_ip = socket.gethostname()
target_ip = target_host[0]
meta_ip = target_host[0]

class TRANSFERENGINE:
    def __init__(self, 
                 mode: str = None,
                 meta_server: str = None,
                 local_server: str = None,
                 local_port: str = None,
                 dev: str = None,
                 vram: bool = False,
                 gpuid: Optional[int] = None,
                 op: str = 'write',
                 block_size: int = DEFAULT_BLOCK_SIZE,
                 batch_size: int = 1000,
                 buffer_size: int = DEFAULT_BUFFER_SIZE,
                 segid: Optional[str] = None):

        # Validate required parameters
        if meta_server is None:
            raise ValueError("meta_server is required")
        if local_server is None:
            raise ValueError("local_server is required")
        if dev is None:
            raise ValueError("dev is required")
        if mode is None:
            raise ValueError("mode is required")
        if op not in ['read', 'write']:
            raise ValueError("op must be either 'read' or 'write'")

        self.mode = mode
        self.meta_server = meta_server
        self.local_server = local_server
        self.local_port = local_port
        self.dev = dev
        self.vram = vram
        self.op = op
        self.block_size = block_size
        self.batch_size = batch_size
        self.buffer_size = buffer_size
        self.gpuid = gpuid
        self.segid = segid
        self.logger = logging.getLogger(__name__)
        self.process = None

    def transfer_start(self):
        """
        Start the transfer engine benchmark process
        
        Returns:
            subprocess.Popen: The started process
            
        Raises:
            RuntimeError: If the process fails to start or encounters an error
        """
        try:
            cmd = [
                'transfer_engine_bench',
                f'--mode={self.mode}',
                f'--metadata_server={self.meta_server}:{ETCD_PORT}',
                f'--local_server_name={self.local_server}:{self.local_port}',
                f'--device_name={self.dev}',
                f'-use_vram={str(self.vram).lower()}',
                f'-operation={self.op}',
                f'-block_size={self.block_size}',
                f'-batch_size={self.batch_size}',
                f'-buffer_size={self.buffer_size}'
            ]
            
            if self.gpuid is not None:
                cmd.append(f'-gpu_id={self.gpuid}')
            if self.segid is not None:
                cmd.append(f'--segment_id={self.segid}')

            self.logger.info(f"Starting transfer engine benchmark: {' '.join(cmd)}")
            
            # Create unique log file name
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_file = f"../results/transfer_engine_{timestamp}_{self.gpuid}.log"
            
            # Run the transfer engine benchmark process
            with open(output_file, 'w') as f:
                f.write(f"Command: {' '.join(cmd)}\n\n")
                self.process = subprocess.Popen(
                    cmd,
                    stdout=f,
                    stderr=f,
                    start_new_session=True
                )
            
            self.logger.info(f"Transfer engine benchmark output is being written to {output_file}")
            return self.process
            
        except Exception as e:
            self.logger.error(f"Failed to start transfer engine benchmark: {e}")
            raise RuntimeError(f"Failed to start transfer engine: {e}")

    def cleanup(self):
        """Clean up the transfer engine process"""
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()

def vram_transfer(mode: str = None, 
                 block_size: int = DEFAULT_BLOCK_SIZE, 
                 batch_size: int = 1000) -> List[subprocess.Popen]:

    processes = []
    instances = []
    
    if len(gpus) != len(devs):
        raise ValueError(f"Number of GPUs ({len(gpus)}) does not match number of devices ({len(devs)})")
    
    try:
        # Create instances for all GPUs
        for i, gpu_id in enumerate(gpus):
            try:
                transfer_engine = TRANSFERENGINE(
                    mode=mode,
                    meta_server=meta_ip,
                    local_server=local_ip,
                    local_port=ports[i],
                    dev=devs[i],
                    vram=True,
                    gpuid=gpu_id,
                    block_size=block_size,
                    batch_size=batch_size,
                    segid=f"{target_ip}:{ports[i]}" if mode is 'initiator' else None
                )
                instances.append(transfer_engine)
            except Exception as e:
                logging.error(f"Failed to create TRANSFERENGINE for GPU {gpu_id}: {e}")
                raise RuntimeError(f"Failed to create transfer engine: {e}")
        
        # Start all transfer processes
        for instance in instances:
            try:
                process = instance.transfer_start()
                processes.append(process)
            except Exception as e:
                logging.error(f"Failed to start transfer for GPU {instance.gpuid}: {e}")
                # Clean up already started processes
                for p in processes:
                    if p and p.poll() is None:
                        p.terminate()
                raise RuntimeError(f"Failed to start transfer: {e}")
        
        return processes
        
    except Exception as e:
        # Clean up all instances in case of error
        for instance in instances:
            instance.cleanup()
        raise

def signal_handler(signum, frame):
    """Handle termination signals"""
    logging.info("Received termination signal. Cleaning up...")
    sys.exit(0)

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    hostname = socket.gethostname()
    
    try:
        # Check if the current hostname is in the target_host list
        if hostname in target_host:
            for batch_size in DEFAULT_BATCH_SIZES:
                vram_transfer(mode='target', block_size=DEFAULT_BLOCK_SIZE, batch_size=batch_size)
        elif hostname in client_host:
            for batch_size in DEFAULT_BATCH_SIZES:
                vram_transfer(mode='initiator', block_size=DEFAULT_BLOCK_SIZE, batch_size=batch_size)
        else:
            logging.error(f"Unexpected hostname: {hostname}")
            sys.exit(1)
    except Exception as e:
        logging.error(f"Error during transfer: {e}")
        sys.exit(1)

    
