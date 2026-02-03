"""Deployment orchestrator implementation."""

import uuid
from pathlib import Path
from typing import Optional

import networkx as nx
import yaml

from spack_ext.deploy.models import DeploymentConfig, Stage


class DeploymentOrchestrator:
    """Orchestrates multi-stage Spack deployments."""

    def __init__(self) -> None:
        """Initialize deployment orchestrator."""
        self.config: Optional[DeploymentConfig] = None
        self.dag: nx.DiGraph = nx.DiGraph()

    def load_config(self, config_file: str) -> None:
        """Load deployment configuration.

        Args:
            config_file: Path to deployment YAML file
        """
        with open(config_file) as f:
            data = yaml.safe_load(f)

        # Handle deployment key if present
        if "deployment" in data:
            config_data = data["deployment"]
        else:
            config_data = data

        self.config = DeploymentConfig(**config_data)
        self._build_dag()

    def _build_dag(self) -> None:
        """Build dependency DAG from stages."""
        if not self.config:
            return

        # Add nodes
        for stage in self.config.stages:
            self.dag.add_node(stage.name, stage=stage)

        # Add edges for dependencies
        for stage in self.config.stages:
            for dep in stage.depends:
                self.dag.add_edge(dep, stage.name)

        # Verify DAG is acyclic
        if not nx.is_directed_acyclic_graph(self.dag):
            raise ValueError("Stage dependencies contain cycles")

    def dry_run(self, stages: Optional[list[str]] = None) -> None:
        """Perform dry run of deployment.

        Args:
            stages: Optional list of specific stages to run
        """
        if not self.config:
            raise ValueError("No configuration loaded")

        print(f"Deployment: {self.config.name}")
        print(f"Base path: {self.config.base_path}")
        print("\nStage execution order:")

        execution_order = list(nx.topological_sort(self.dag))

        if stages:
            execution_order = [s for s in execution_order if s in stages]

        for i, stage_name in enumerate(execution_order, 1):
            stage_data = self.dag.nodes[stage_name]["stage"]
            print(f"  {i}. {stage_name}")
            print(f"     Environment: {stage_data.environment}")
            print(f"     Depends on: {', '.join(stage_data.depends) or 'none'}")
            print(f"     Parallel: {stage_data.parallel}")

    def execute(self, stages: Optional[list[str]] = None) -> str:
        """Execute deployment pipeline.

        Args:
            stages: Optional list of specific stages to run

        Returns:
            Deployment ID
        """
        if not self.config:
            raise ValueError("No configuration loaded")

        deployment_id = str(uuid.uuid4())[:8]

        print(f"Starting deployment {deployment_id}")
        print(f"Deployment: {self.config.name}")

        execution_order = list(nx.topological_sort(self.dag))

        if stages:
            execution_order = [s for s in execution_order if s in stages]

        for stage_name in execution_order:
            stage_data: Stage = self.dag.nodes[stage_name]["stage"]
            print(f"\nExecuting stage: {stage_name}")
            print(f"  Environment: {stage_data.environment}")

            # In a real implementation, this would:
            # 1. Load the Spack environment
            # 2. Install packages
            # 3. Generate modules
            # 4. Collect artifacts

            print(f"  Status: Complete (simulated)")

        return deployment_id

    def get_status(self, deployment_id: str) -> dict[str, str]:
        """Get deployment status.

        Args:
            deployment_id: Deployment ID to query

        Returns:
            Status information
        """
        return {
            "deployment_id": deployment_id,
            "status": "completed",
            "message": "Deployment orchestration simulated",
        }
