"""This module initializes Opik tracing for observability."""
import opik


def init_observability():
    """
    Initializes Opik tracing.
    Safe to call multiple times.
    """
    opik.configure(
        project_name="v2-flight-comparison",
        trace_all=True,
    )
