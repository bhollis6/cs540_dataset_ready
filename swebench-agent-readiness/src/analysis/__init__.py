"""Analysis packet contracts for the SWE-bench pivot."""

from .comparison_packet import (
    ComparisonPacket,
    ConditionOutcome,
    build_comparison_packet,
    write_comparison_packet,
)
from .oracle_packet import (
    OracleComparisonArtifact,
    build_oracle_comparison_artifact,
    write_oracle_comparison_artifact,
)

__all__ = [
    "ComparisonPacket",
    "ConditionOutcome",
    "OracleComparisonArtifact",
    "build_comparison_packet",
    "build_oracle_comparison_artifact",
    "write_comparison_packet",
    "write_oracle_comparison_artifact",
]
