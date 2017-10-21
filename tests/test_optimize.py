"""
Tests for the OptimizationWorkChain.
"""

import numpy as np


def test_optimize_run(configure, submit_as_async):  # pylint: disable=unused-argument
    """
    Simple test of the OptimizationWorkChain, with the Bisection engine.
    """
    from echo_workchain import Echo
    from aiida_optimize.engines import Bisection
    from aiida_optimize.workchain import OptimizationWorkChain
    from aiida.orm.data.parameter import ParameterData
    tolerance = 1e-1
    result = OptimizationWorkChain.run(
        engine=Bisection,
        engine_kwargs=ParameterData(
            dict=dict(lower=-1, upper=1, tol=tolerance)
        ),
        calculation_workchain=Echo
    )['optimizer_result']
    assert np.isclose(result.value, 0, atol=tolerance)
