"""
Workflow Coordinator - Multi-Agent Execution Management
Handles complex multi-step workflows with state management and error recovery
"""

import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from src.utils.logging import get_logger

logger = get_logger(__name__)


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowStatus(Enum):
    """Overall workflow status"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PARTIALLY_COMPLETED = "partially_completed"
    FAILED = "failed"


@dataclass
class WorkflowTask:
    """Individual task in a workflow"""
    task_id: str
    agent_name: str
    query: str
    dependencies: List[str]  # List of task_ids that must complete first
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[str] = None
    error: Optional[str] = None
    requires_confirmation: bool = False
    risk_level: str = "LOW"  # LOW, MEDIUM, HIGH, CRITICAL


@dataclass
class WorkflowDefinition:
    """Complete workflow definition"""
    workflow_id: str
    name: str
    description: str
    tasks: List[WorkflowTask]
    created_by: str
    ticket_number: Optional[str] = None


class WorkflowCoordinator:
    """
    Workflow Coordinator - Manages multi-agent workflow execution
    
    Responsibilities:
    - Execute tasks in dependency order
    - Handle parallel execution when possible
    - Manage workflow state
    - Handle confirmations and interruptions
    - Retry failed tasks
    - Aggregate results
    - Generate workflow reports
    """
    
    def __init__(self, orchestrator_agent):
        """
        Initialize Workflow Coordinator
        
        Args:
            orchestrator_agent: MasterOrchestrator instance for A2A communication
        """
        self.orchestrator = orchestrator_agent
        self.active_workflows: Dict[str, WorkflowDefinition] = {}
        
    async def execute_workflow(
        self,
        workflow: WorkflowDefinition,
        confirmation_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Execute a complete workflow with state management
        
        Args:
            workflow: WorkflowDefinition to execute
            confirmation_callback: Function to call for user confirmations
            
        Returns:
            Dict with execution results and status
        """
        logger.info(f"Starting workflow: {workflow.name} (ID: {workflow.workflow_id})")
        self.active_workflows[workflow.workflow_id] = workflow
        
        results = {
            "workflow_id": workflow.workflow_id,
            "name": workflow.name,
            "status": WorkflowStatus.IN_PROGRESS,
            "tasks": {},
            "completed_count": 0,
            "failed_count": 0,
            "skipped_count": 0,
            "total_count": len(workflow.tasks),
        }
        
        try:
            # Build dependency graph
            task_map = {task.task_id: task for task in workflow.tasks}
            
            # Execute tasks in dependency order
            while not self._all_tasks_done(workflow):
                # Find tasks ready to execute (dependencies satisfied)
                ready_tasks = self._get_ready_tasks(workflow, task_map)
                
                if not ready_tasks:
                    # Check if we're stuck
                    if self._has_pending_tasks(workflow):
                        logger.error("Workflow deadlock detected - circular dependencies or all remaining tasks failed")
                        results["status"] = WorkflowStatus.FAILED
                        results["error"] = "Workflow deadlock: No tasks can proceed"
                        break
                    else:
                        break  # All done
                
                # Execute ready tasks in parallel
                await self._execute_tasks_parallel(
                    ready_tasks,
                    task_map,
                    results,
                    confirmation_callback
                )
            
            # Determine final status
            results["completed_count"] = sum(
                1 for t in workflow.tasks if t.status == TaskStatus.COMPLETED
            )
            results["failed_count"] = sum(
                1 for t in workflow.tasks if t.status == TaskStatus.FAILED
            )
            results["skipped_count"] = sum(
                1 for t in workflow.tasks if t.status == TaskStatus.SKIPPED
            )
            
            if results["completed_count"] == results["total_count"]:
                results["status"] = WorkflowStatus.COMPLETED
            elif results["completed_count"] > 0:
                results["status"] = WorkflowStatus.PARTIALLY_COMPLETED
            else:
                results["status"] = WorkflowStatus.FAILED
            
            logger.info(
                f"Workflow complete: {workflow.name} - "
                f"{results['completed_count']}/{results['total_count']} tasks succeeded"
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Workflow execution error: {e}", exc_info=True)
            results["status"] = WorkflowStatus.FAILED
            results["error"] = str(e)
            return results
        finally:
            # Cleanup
            if workflow.workflow_id in self.active_workflows:
                del self.active_workflows[workflow.workflow_id]
    
    async def _execute_tasks_parallel(
        self,
        tasks: List[WorkflowTask],
        task_map: Dict[str, WorkflowTask],
        results: Dict,
        confirmation_callback: Optional[callable]
    ):
        """Execute multiple tasks in parallel"""
        task_coroutines = []
        
        for task in tasks:
            task_coroutines.append(
                self._execute_single_task(task, task_map, results, confirmation_callback)
            )
        
        # Run tasks concurrently
        await asyncio.gather(*task_coroutines, return_exceptions=True)
    
    async def _execute_single_task(
        self,
        task: WorkflowTask,
        task_map: Dict[str, WorkflowTask],
        results: Dict,
        confirmation_callback: Optional[callable]
    ):
        """Execute a single task with error handling"""
        try:
            task.status = TaskStatus.IN_PROGRESS
            logger.info(f"Executing task {task.task_id}: {task.agent_name}")
            
            # Check if confirmation required
            if task.requires_confirmation and confirmation_callback:
                confirmation_prompt = (
                    f"Task: {task.query}\n"
                    f"Agent: {task.agent_name}\n"
                    f"Risk: {task.risk_level}\n"
                    f"Confirm execution? (yes/no)"
                )
                
                confirmed = await confirmation_callback(confirmation_prompt)
                
                if not confirmed:
                    task.status = TaskStatus.SKIPPED
                    task.result = "Skipped by user"
                    logger.info(f"Task {task.task_id} skipped by user")
                    results["tasks"][task.task_id] = {
                        "status": "skipped",
                        "reason": "User declined confirmation"
                    }
                    return
            
            # Execute task via orchestrator
            # In a real implementation, this would use A2A to call the specific agent
            # For now, we'll use the orchestrator's query method which will route to correct agent
            result = await self.orchestrator.query(
                f"[{task.agent_name}] {task.query}"
            )
            
            task.status = TaskStatus.COMPLETED
            task.result = result
            results["tasks"][task.task_id] = {
                "status": "completed",
                "result": result,
                "agent": task.agent_name
            }
            
            logger.info(f"✓ Task {task.task_id} completed successfully")
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            results["tasks"][task.task_id] = {
                "status": "failed",
                "error": str(e),
                "agent": task.agent_name
            }
            
            logger.error(f"✗ Task {task.task_id} failed: {e}")
            
            # Mark dependent tasks as skipped
            self._skip_dependent_tasks(task.task_id, task_map)
    
    def _get_ready_tasks(
        self,
        workflow: WorkflowDefinition,
        task_map: Dict[str, WorkflowTask]
    ) -> List[WorkflowTask]:
        """Find tasks that are ready to execute (all dependencies satisfied)"""
        ready = []
        
        for task in workflow.tasks:
            if task.status != TaskStatus.PENDING:
                continue
            
            # Check if all dependencies are completed
            dependencies_met = all(
                task_map[dep_id].status == TaskStatus.COMPLETED
                for dep_id in task.dependencies
                if dep_id in task_map
            )
            
            if dependencies_met:
                ready.append(task)
        
        return ready
    
    def _all_tasks_done(self, workflow: WorkflowDefinition) -> bool:
        """Check if all tasks are in a terminal state"""
        terminal_states = {
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.SKIPPED
        }
        return all(task.status in terminal_states for task in workflow.tasks)
    
    def _has_pending_tasks(self, workflow: WorkflowDefinition) -> bool:
        """Check if any tasks are still pending"""
        return any(
            task.status == TaskStatus.PENDING
            for task in workflow.tasks
        )
    
    def _skip_dependent_tasks(
        self,
        failed_task_id: str,
        task_map: Dict[str, WorkflowTask]
    ):
        """Skip tasks that depend on a failed task"""
        for task in task_map.values():
            if failed_task_id in task.dependencies and task.status == TaskStatus.PENDING:
                task.status = TaskStatus.SKIPPED
                task.result = f"Skipped due to failed dependency: {failed_task_id}"
                logger.info(f"Skipping task {task.task_id} due to failed dependency")
    
    def generate_workflow_report(self, workflow_id: str) -> str:
        """Generate a human-readable workflow execution report"""
        if workflow_id not in self.active_workflows:
            return f"Workflow {workflow_id} not found"
        
        workflow = self.active_workflows[workflow_id]
        
        report = []
        report.append("=" * 80)
        report.append(f"WORKFLOW REPORT: {workflow.name}")
        report.append("=" * 80)
        report.append(f"ID: {workflow.workflow_id}")
        report.append(f"Description: {workflow.description}")
        if workflow.ticket_number:
            report.append(f"Ticket: {workflow.ticket_number}")
        report.append("")
        
        # Status summary
        completed = sum(1 for t in workflow.tasks if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in workflow.tasks if t.status == TaskStatus.FAILED)
        skipped = sum(1 for t in workflow.tasks if t.status == TaskStatus.SKIPPED)
        pending = sum(1 for t in workflow.tasks if t.status == TaskStatus.PENDING)
        
        report.append("STATUS SUMMARY:")
        report.append(f"  ✓ Completed: {completed}/{len(workflow.tasks)}")
        if failed > 0:
            report.append(f"  ✗ Failed: {failed}")
        if skipped > 0:
            report.append(f"  ⊘ Skipped: {skipped}")
        if pending > 0:
            report.append(f"  ⏳ Pending: {pending}")
        report.append("")
        
        # Task details
        report.append("TASK DETAILS:")
        for i, task in enumerate(workflow.tasks, 1):
            status_icon = {
                TaskStatus.COMPLETED: "✓",
                TaskStatus.FAILED: "✗",
                TaskStatus.SKIPPED: "⊘",
                TaskStatus.PENDING: "⏳",
                TaskStatus.IN_PROGRESS: "⏳",
            }[task.status]
            
            report.append(f"{i}. {status_icon} {task.task_id}")
            report.append(f"   Agent: {task.agent_name}")
            report.append(f"   Query: {task.query}")
            report.append(f"   Status: {task.status.value}")
            
            if task.dependencies:
                report.append(f"   Dependencies: {', '.join(task.dependencies)}")
            
            if task.result:
                result_preview = task.result[:100] + "..." if len(task.result) > 100 else task.result
                report.append(f"   Result: {result_preview}")
            
            if task.error:
                report.append(f"   Error: {task.error}")
            
            report.append("")
        
        return "\n".join(report)


# Pre-defined workflow templates
class WorkflowTemplates:
    """Common IT Service Desk workflow templates"""
    
    @staticmethod
    def password_reset_and_verify(user_email: str) -> WorkflowDefinition:
        """Password reset with sign-in verification"""
        return WorkflowDefinition(
            workflow_id=f"pwd_reset_{user_email}",
            name="Password Reset & Verification",
            description=f"Reset password for {user_email} and verify resolution",
            created_by="system",
            tasks=[
                WorkflowTask(
                    task_id="check_user",
                    agent_name="ADUserLookupAgent",
                    query=f"Get info for {user_email}",
                    dependencies=[],
                    risk_level="LOW"
                ),
                WorkflowTask(
                    task_id="reset_password",
                    agent_name="ADPasswordResetAgent",
                    query=f"Reset password for {user_email}",
                    dependencies=["check_user"],
                    requires_confirmation=True,
                    risk_level="MEDIUM"
                ),
                WorkflowTask(
                    task_id="verify_signin",
                    agent_name="SignInAnalysisAgent",
                    query=f"Check recent sign-in logs for {user_email}",
                    dependencies=["reset_password"],
                    risk_level="LOW"
                ),
            ]
        )
    
    @staticmethod
    def device_compliance_fix(device_name: str, user_email: str) -> WorkflowDefinition:
        """Check and fix device compliance issues"""
        return WorkflowDefinition(
            workflow_id=f"compliance_fix_{device_name}",
            name="Device Compliance Troubleshooting",
            description=f"Diagnose and fix compliance issues for {device_name}",
            created_by="system",
            tasks=[
                WorkflowTask(
                    task_id="check_compliance",
                    agent_name="ComplianceCheckAgent",
                    query=f"Check compliance status for {device_name}",
                    dependencies=[],
                    risk_level="LOW"
                ),
                WorkflowTask(
                    task_id="sync_device",
                    agent_name="RemoteActionsAgent",
                    query=f"Sync device {device_name} to re-evaluate compliance",
                    dependencies=["check_compliance"],
                    risk_level="LOW"
                ),
                WorkflowTask(
                    task_id="verify_fixed",
                    agent_name="ComplianceCheckAgent",
                    query=f"Re-check compliance for {device_name} after sync",
                    dependencies=["sync_device"],
                    risk_level="LOW"
                ),
            ]
        )
    
    @staticmethod
    def new_employee_setup(user_email: str, department: str) -> WorkflowDefinition:
        """New employee onboarding workflow"""
        return WorkflowDefinition(
            workflow_id=f"onboard_{user_email}",
            name="New Employee Onboarding",
            description=f"Complete setup for new employee {user_email}",
            created_by="system",
            tasks=[
                WorkflowTask(
                    task_id="verify_ad_account",
                    agent_name="ADUserLookupAgent",
                    query=f"Check if {user_email} exists in AD",
                    dependencies=[],
                    risk_level="LOW"
                ),
                WorkflowTask(
                    task_id="assign_license",
                    agent_name="LicenseManagementAgent",
                    query=f"Assign Office 365 E3 license to {user_email}",
                    dependencies=["verify_ad_account"],
                    requires_confirmation=True,
                    risk_level="MEDIUM"
                ),
                WorkflowTask(
                    task_id="add_to_groups",
                    agent_name="GroupMembershipAgent",
                    query=f"Add {user_email} to VPN-Users and {department}-Team groups",
                    dependencies=["verify_ad_account"],
                    requires_confirmation=True,
                    risk_level="MEDIUM"
                ),
                WorkflowTask(
                    task_id="create_ticket",
                    agent_name="IncidentCreationAgent",
                    query=f"Create onboarding tracking ticket for {user_email}",
                    dependencies=["assign_license", "add_to_groups"],
                    risk_level="LOW"
                ),
            ]
        )
    
    @staticmethod
    def employee_offboarding(user_email: str) -> WorkflowDefinition:
        """Employee termination workflow"""
        return WorkflowDefinition(
            workflow_id=f"offboard_{user_email}",
            name="Employee Offboarding",
            description=f"Remove access and reclaim resources for {user_email}",
            created_by="system",
            tasks=[
                WorkflowTask(
                    task_id="list_devices",
                    agent_name="DeviceInventoryAgent",
                    query=f"List all devices for {user_email}",
                    dependencies=[],
                    risk_level="LOW"
                ),
                WorkflowTask(
                    task_id="remove_licenses",
                    agent_name="LicenseManagementAgent",
                    query=f"Remove all licenses from {user_email}",
                    dependencies=[],
                    requires_confirmation=True,
                    risk_level="MEDIUM"
                ),
                WorkflowTask(
                    task_id="wipe_devices",
                    agent_name="RemoteActionsAgent",
                    query=f"Wipe all company devices for {user_email}",
                    dependencies=["list_devices"],
                    requires_confirmation=True,
                    risk_level="CRITICAL"
                ),
                WorkflowTask(
                    task_id="create_ticket",
                    agent_name="IncidentCreationAgent",
                    query=f"Create offboarding completion ticket for {user_email}",
                    dependencies=["remove_licenses", "wipe_devices"],
                    risk_level="LOW"
                ),
            ]
        )
