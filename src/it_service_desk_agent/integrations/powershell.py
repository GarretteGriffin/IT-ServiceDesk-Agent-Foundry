"""PowerShell executor - single place for subprocess execution"""

import asyncio
from typing import List
import logging

logger = logging.getLogger(__name__)


class PowerShellExecutor:
    """
    PowerShell script executor
    
    Security notes:
    - Runs with current user credentials
    - No input sanitization here (caller must validate)
    - For production: Use Azure Automation Runbooks or constrained PowerShell endpoints
    """
    
    def __init__(self, base_script_path: str = ".") -> None:
        """
        Initialize executor
        
        Args:
            base_script_path: Base directory for PowerShell scripts
        """
        self._base_script_path = base_script_path
        logger.info(f"Initialized PowerShell executor with base path: {base_script_path}")
    
    async def run_script(self, script_name: str, args: List[str]) -> str:
        """
        Run PowerShell script from file
        
        Args:
            script_name: Script filename (relative to base_script_path)
            args: Arguments to pass to script
        
        Returns:
            Script stdout
        
        Raises:
            RuntimeError: If script fails
        """
        script_path = f"{self._base_script_path}/{script_name}"
        logger.info(f"Running PowerShell script: {script_path} with args: {args}")
        
        process = await asyncio.create_subprocess_exec(
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy", "Bypass",
            "-File", script_path,
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error = stderr.decode('utf-8').strip()
            logger.error(f"PowerShell script failed: {error}")
            raise RuntimeError(f"PowerShell script failed ({script_name}): {error}")
        
        result = stdout.decode('utf-8').strip()
        logger.info(f"PowerShell script completed: {len(result)} bytes output")
        return result
    
    async def run_command(self, command: str) -> str:
        """
        Run PowerShell command directly
        
        Args:
            command: PowerShell command to execute
        
        Returns:
            Command stdout
        
        Raises:
            RuntimeError: If command fails
        """
        logger.info(f"Running PowerShell command (first 100 chars): {command[:100]}...")
        
        process = await asyncio.create_subprocess_exec(
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy", "Bypass",
            "-Command", command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error = stderr.decode('utf-8').strip()
            logger.error(f"PowerShell command failed: {error}")
            raise RuntimeError(f"PowerShell command failed: {error}")
        
        result = stdout.decode('utf-8').strip()
        logger.info(f"PowerShell command completed: {len(result)} bytes output")
        return result
