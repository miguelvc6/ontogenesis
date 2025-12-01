import docker
import os
import tempfile
import json
from typing import Any, Dict, Optional
from utils.tracer import tracer

class DockerRunner:
    """
    Executes code in an isolated Docker container.
    """
    def __init__(self, image: str = "python:3.12-slim"):
        self.image = image
        # Try to connect to Docker daemon on Windows named pipe
        try:
            self.client = docker.DockerClient(base_url='npipe:////./pipe/docker_engine')
        except Exception:
            # Fallback to default environment
            self.client = docker.from_env()
        tracer.log_event("docker_runner_init", {"image": image})
        
        # Ensure image exists
        try:
            self.client.images.get(image)
        except docker.errors.ImageNotFound:
            print(f"Pulling Docker image: {image}...")
            self.client.images.pull(image)

    def run_code(self, code: str, entry_point: str, input_data: Any = None, **kwargs) -> Any:
        """
        Executes the given code in a Docker container.
        
        Strategy:
        1. Create a temporary directory.
        2. Write the code to `script.py`.
        3. Write a wrapper script `main.py` that imports `script`, calls `entry_point`, and prints the result as JSON.
        4. Mount the temp dir to the container.
        5. Run the container and capture stdout.
        """
        tracer.start_span("run_code_docker", {"entry_point": entry_point, "image": self.image})
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # 1. Write User Code
            script_path = os.path.join(temp_dir, "script.py")
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(code)
                
            # 2. Prepare Input Data
            input_json = json.dumps(input_data) if input_data is not None else "null"
            
            # 3. Write Wrapper Script
            wrapper_code = f"""
import sys
import json
import script
from bs4 import BeautifulSoup # Ensure dependencies are available

def main():
    try:
        # Load input
        input_data = {input_json}
        
        # Call entry point
        result = script.{entry_point}(input_data)
        
        # Print result as JSON
        print(json.dumps(result))
        
    except Exception as e:
        print(f"ERROR: {{e}}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
"""
            wrapper_path = os.path.join(temp_dir, "wrapper.py")
            with open(wrapper_path, "w", encoding="utf-8") as f:
                f.write(wrapper_code)

            # 4. Run Container
            try:
                # We need to install bs4 if it's not in the base image
                # For efficiency, we should build a custom image, but for now we'll pip install on the fly (slow)
                # OR assume the user provides an image with dependencies.
                # Let's use a simple command that installs dependencies first.
                command = "sh -c 'pip install beautifulsoup4 > /dev/null 2>&1 && python /app/wrapper.py'"
                
                logs = self.client.containers.run(
                    self.image,
                    command=command,
                    volumes={temp_dir: {'bind': '/app', 'mode': 'rw'}},
                    working_dir='/app',
                    remove=True,
                    stderr=True
                )
                
                output = logs.decode("utf-8").strip()
                
                # Parse Result
                try:
                    result = json.loads(output)
                    tracer.end_span(outputs="Execution successful")
                    return result
                except json.JSONDecodeError:
                    tracer.end_span(error=f"Invalid JSON output: {output}")
                    raise RuntimeError(f"Execution failed (Invalid JSON): {output}")
                    
            except docker.errors.ContainerError as e:
                error_msg = e.stderr.decode("utf-8") if e.stderr else str(e)
                tracer.end_span(error=f"Container error: {error_msg}")
                raise RuntimeError(f"Container execution failed: {error_msg}")
            except Exception as e:
                tracer.end_span(error=str(e))
                raise RuntimeError(f"Docker execution failed: {e}")

    def verify_result(self, result: Any, test_code: str) -> bool:
        """
        Verifies the result using the provided pytest code.
        """
        tracer.start_span("verify_result_docker", {"image": self.image})
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # 1. Write Result
            with open(os.path.join(temp_dir, "result.json"), "w", encoding="utf-8") as f:
                json.dump(result, f)
                
            # 2. Write Test Code
            with open(os.path.join(temp_dir, "test_generated.py"), "w", encoding="utf-8") as f:
                f.write(test_code)
                
            # 3. Run Pytest
            try:
                # Install pytest if needed (slow, but robust)
                command = "sh -c 'pip install pytest > /dev/null 2>&1 && pytest /app/test_generated.py'"
                
                # Run and capture output
                logs = self.client.containers.run(
                    self.image,
                    command=command,
                    volumes={temp_dir: {'bind': '/app', 'mode': 'rw'}},
                    working_dir='/app',
                    remove=True,
                    stderr=True,
                    stdout=True
                )
                
                tracer.end_span(outputs="Verification passed")
                return True
                
            except docker.errors.ContainerError as e:
                # Pytest failed (exit code 1)
                # Capture both stdout (logs) and stderr
                # Note: 'e.container' might be gone if remove=True? 
                # Actually, e.stderr contains stderr. e.stdout? 
                # The 'logs' variable above is not assigned if exception is raised.
                # But ContainerError has a 'stderr' attribute. Does it have stdout?
                # It seems ContainerError usually only has stderr if we asked for it?
                # Let's try to be safer.
                
                # Wait, if I use detach=False (default), it returns logs.
                # If it fails, it raises ContainerError.
                # ContainerError has 'container', 'exit_status', 'command', 'image', 'stderr'.
                # It does NOT seem to have stdout easily accessible if it's mixed?
                # Actually, if I don't redirect stdout to /dev/null, it should be in the output.
                
                # Let's try to capture output manually by not using 'run' helper if possible?
                # Or just trust that stderr might contain it if configured?
                # Pytest prints to stdout.
                
                # Better approach: Run the container with detach=True, wait, then get logs.
                container = self.client.containers.run(
                    self.image,
                    command=command,
                    volumes={temp_dir: {'bind': '/app', 'mode': 'rw'}},
                    working_dir='/app',
                    detach=True,
                    stderr=True,
                    stdout=True
                )
                
                result = container.wait()
                logs = container.logs().decode("utf-8")
                container.remove()
                
                if result["StatusCode"] != 0:
                    tracer.end_span(error=f"Verification failed: {logs}")
                    raise RuntimeError(f"Verification failed: {logs}")
                
                tracer.end_span(outputs="Verification passed")
                return True
            except Exception as e:
                tracer.end_span(error=str(e))
                raise RuntimeError(f"Docker verification failed: {e}")
