"""Experiment runner: grid search over representations x metrics x algorithms x K.

Orchestrates the full experiment pipeline described in the project plan.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import networkx as nx
import pandas as pd

from src.clustering.base import CantonAssignment, SpatialClusterer
from src.data.distance_metrics import DistanceMetric
from src.data.representations import Representation, PCARepresentation
from src.evaluation.metrics import evaluate_all

logger = logging.getLogger(__name__)


@dataclass
class ExperimentConfig:
    """One combination of representation + metric + algorithm + K."""

    representation: Representation
    distance_metric: DistanceMetric
    clusterer: SpatialClusterer
    k: int

    @property
    def label(self) -> str:
        return (
            f"{self.representation.name}__{self.distance_metric.name}"
            f"__{self.clusterer.name}__k{self.k}"
        )


@dataclass
class ExperimentResult:
    config: ExperimentConfig
    assignment: CantonAssignment | None = None
    metrics: dict = field(default_factory=dict)
    elapsed_seconds: float = 0.0
    error: str | None = None


class ExperimentRunner:
    """Run a grid of experiments over multiple configurations."""

    def __init__(
        self,
        representations: list[Representation],
        distance_metrics: list[DistanceMetric],
        clusterers: list[SpatialClusterer],
        k_values: list[int],
        elections: dict[int, pd.DataFrame],
        graph: nx.Graph,
        weights: dict[str, float],
    ) -> None:
        self.representations = representations
        self.distance_metrics = distance_metrics
        self.clusterers = clusterers
        self.k_values = k_values
        self.elections = elections
        self.graph = graph
        self.weights = weights

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def _is_compatible(self, config: ExperimentConfig) -> bool:
        """Check if representation + metric combo is valid."""
        # JSD requires non-negative features → incompatible with PCA
        if config.distance_metric.name == "jensen_shannon":
            if isinstance(config.representation, PCARepresentation):
                return False
        return True

    def build_configs(self) -> list[ExperimentConfig]:
        """Generate all valid experiment configurations."""
        configs: list[ExperimentConfig] = []
        for rep in self.representations:
            for met in self.distance_metrics:
                for clust in self.clusterers:
                    for k in self.k_values:
                        cfg = ExperimentConfig(rep, met, clust, k)
                        if self._is_compatible(cfg):
                            configs.append(cfg)
        return configs

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def run_single(self, config: ExperimentConfig) -> ExperimentResult:
        """Run one experiment configuration."""
        t0 = time.time()
        try:
            features = config.representation.fit_transform(self.elections)
            feature_cols = config.representation.feature_names

            assignment = config.clusterer.fit(
                features=features,
                feature_cols=feature_cols,
                graph=self.graph,
                k=config.k,
                distance_metric=config.distance_metric,
                weights=self.weights,
            )

            metrics = evaluate_all(
                assignment=assignment,
                features=features,
                feature_cols=feature_cols,
                graph=self.graph,
                weights=self.weights,
            )

            elapsed = time.time() - t0
            return ExperimentResult(
                config=config,
                assignment=assignment,
                metrics=metrics,
                elapsed_seconds=elapsed,
            )
        except Exception as exc:
            elapsed = time.time() - t0
            logger.exception("Experiment %s failed", config.label)
            return ExperimentResult(
                config=config,
                elapsed_seconds=elapsed,
                error=str(exc),
            )

    def run_all(
        self, save_dir: Path | None = None
    ) -> pd.DataFrame:
        """Run all valid experiments and return results DataFrame."""
        configs = self.build_configs()
        logger.info("Running %d experiments", len(configs))

        rows: list[dict] = []
        for i, cfg in enumerate(configs):
            logger.info("[%d/%d] %s", i + 1, len(configs), cfg.label)
            result = self.run_single(cfg)

            row: dict[str, Any] = {
                "repr": cfg.representation.name,
                "metric": cfg.distance_metric.name,
                "algo": cfg.clusterer.name,
                "k_target": cfg.k,
                "k_actual": result.assignment.k if result.assignment else None,
                "elapsed_s": round(result.elapsed_seconds, 2),
                "error": result.error,
            }
            row.update(
                {k: v for k, v in result.metrics.items()
                 if not isinstance(v, (dict, list))}
            )
            rows.append(row)

            # Optionally save each assignment
            if save_dir and result.assignment:
                save_dir.mkdir(parents=True, exist_ok=True)
                result.assignment.to_dataframe().to_csv(
                    save_dir / f"{cfg.label}.csv", index=False
                )

        df = pd.DataFrame(rows)
        if save_dir:
            df.to_csv(save_dir / "experiment_results.csv", index=False)
        return df
