# -*- coding: utf-8 -*-
"""
Tests for the ConcatenateWorkChain.
"""

# pylint: disable=unused-argument,redefined-outer-name,invalid-name
import pytest

from aiida import orm
from aiida.plugins import WorkflowFactory
from aiida.engine.launch import run_get_node

from aiida_tools.process_inputs import get_fullname

from sample_processes import echo_process, Echo, EchoDictValue, EchoNestedValues  # pylint: disable=import-error,useless-suppression, unused-import


def test_concatenate_basic(configure_with_daemon, echo_process):
    """
    Test the ConcatenateWorkChain by chaining three basic processes.
    """

    ConcatenateWorkChain = WorkflowFactory('optimize.wrappers.concatenate')  # pylint: disable=invalid-name

    res, node = run_get_node(
        ConcatenateWorkChain,
        process_labels=orm.List(
            list=[
                ('one', get_fullname(echo_process).value),
                ('two', get_fullname(echo_process).value),
                ('three', get_fullname(echo_process).value),
            ]
        ),
        process_inputs={'one': {
            'x': orm.Float(1)
        }},
        output_input_mappings=orm.List(list=[{
            'result': 'x'
        }, {
            'result': 'x'
        }])
    )
    assert node.is_finished_ok

    assert 'one' in res['process_outputs']
    assert 'two' in res['process_outputs']
    assert 'three' in res['process_outputs']

    assert 'result' in res['process_outputs']['one']
    assert 'result' in res['process_outputs']['two']
    assert 'result' in res['process_outputs']['three']

    assert res['process_outputs']['one']['result'].value == 1
    assert res['process_outputs']['two']['result'].value == 1
    assert res['process_outputs']['three']['result'].value == 1


def test_concatenate_inconsistent_input_length(configure_with_daemon):
    """
    The 'output_input_mapping' input is too short, needs to raise.
    """

    ConcatenateWorkChain = WorkflowFactory('optimize.wrappers.concatenate')  # pylint: disable=invalid-name

    with pytest.raises(ValueError) as exc:
        run_get_node(
            ConcatenateWorkChain,
            process_labels=orm.List(
                list=[
                    ('one', get_fullname(Echo).value),
                    ('two', get_fullname(Echo).value),
                    ('three', get_fullname(Echo).value),
                ]
            ),
            process_inputs={'one': {
                'x': orm.Float(1)
            }},
            output_input_mappings=orm.List(list=[{
                'result': 'x'
            }])
        )
    assert 'inconsistent length' in str(exc.value)


def test_concatenate_invalid_input_label(configure_with_daemon):
    """
    The 'output_input_mapping' input is too short, needs to raise.
    """

    ConcatenateWorkChain = WorkflowFactory('optimize.wrappers.concatenate')  # pylint: disable=invalid-name

    with pytest.raises(ValueError) as exc:
        run_get_node(
            ConcatenateWorkChain,
            process_labels=orm.List(
                list=[
                    ('one', get_fullname(Echo).value),
                    ('two', get_fullname(Echo).value),
                    ('three', get_fullname(Echo).value),
                ]
            ),
            process_inputs={
                'one': {
                    'x': orm.Float(1)
                },
                'invalid_label': {
                    'x': orm.Float(2.)
                }
            },
            output_input_mappings=orm.List(list=[{
                'result': 'x'
            }, {
                'result': 'x'
            }])
        )
    assert "does not match any of the 'process_labels'" in str(exc.value)


def test_concatenate_nested_keys(configure_with_daemon):
    """Concatenate processes with nested input and output keys.
    """
    ConcatenateWorkChain = WorkflowFactory('optimize.wrappers.concatenate')  # pylint: disable=invalid-name

    res, node = run_get_node(
        ConcatenateWorkChain,
        process_labels=orm.List(
            list=[
                ('one', get_fullname(EchoNestedValues).value),
                ('two', get_fullname(EchoNestedValues).value),
                ('three', get_fullname(EchoDictValue).value),
            ]
        ),
        process_inputs={
            'one': {
                'x': {
                    'y': orm.Float(1)
                },
                'a': {
                    'b': {
                        'c': {
                            'd': orm.Dict(dict=dict({'e': {
                                'f': 2
                            }}))
                        }
                    }
                }
            },
            'three': {
                'a': orm.Dict(dict={'b': {
                    'c': 3
                }})
            }
        },
        output_input_mappings=orm.List(
            list=[{
                'y': 'a.b.c.d:e.f',
                'f': 'x.y',
            }, {
                'y': 'x',
                'f': 'f.g',
            }]
        )
    )
    assert node.is_finished_ok

    assert 'one' in res['process_outputs']
    assert 'two' in res['process_outputs']
    assert 'three' in res['process_outputs']

    assert res['process_outputs']['one']['y'].value == 1
    assert res['process_outputs']['one']['f'].value == 2

    assert res['process_outputs']['two']['y'].value == 2
    assert res['process_outputs']['two']['f'].value == 1

    assert res['process_outputs']['three']['x'].value == 2
    assert res['process_outputs']['three']['c'].value == 3
    assert res['process_outputs']['three']['d']['e'].get_dict() == {'f': {'g': 1}}