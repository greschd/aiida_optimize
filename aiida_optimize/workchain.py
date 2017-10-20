from contextlib import contextmanager

from fsc.export import export
from aiida_tools.workchain_inputs import WORKCHAIN_INPUT_KWARGS

from aiida.orm.data.base import Float
from aiida.orm.data.parameter import ParameterData
from aiida.work.workchain import WorkChain, ToContext, while_
from aiida.work import submit

from aiida_tools import check_workchain_step


@export
class OptimizationWorkChain(WorkChain):
    """
    TODO
    """
    _CALC_PREFIX = 'calc_'

    @classmethod
    def define(cls, spec):
        super(cls, OptimizationWorkChain).define(spec)

        spec.input(
            'engine',
            help='Engine that runs the optimization.',
            **WORKCHAIN_INPUT_KWARGS
        )
        spec.input(
            'engine_kwargs',
            valid_type=ParameterData,
            help='Keyword arguments passed to the optimization engine.'
        )
        spec.input(
            'calculation_workchain',
            help='WorkChain which produces the result to be optimized.',
            **WORKCHAIN_INPUT_KWARGS
        )

        spec.outline(
            cls.create_optimizer,
            while_(cls.not_finished)(cls.launch_calculations, cls.get_results),
            cls.finalize
        )
        spec.output('result', valid_type=Float)

    @contextmanager
    def optimizer(self):
        optimizer = self.engine.from_state(self.ctx.optimizer_state)
        yield optimizer
        self.ctx.optimizer_state = optimizer.state

    @property
    def engine(self):
        return self.get_deserialized_input('engine')

    @check_workchain_step
    def create_optimizer(self):
        optimizer = self.engine(**self.inputs.engine_kwargs.get_dict())
        self.ctx.optimizer_state = optimizer.state

    @check_workchain_step
    def not_finished(self):
        with self.optimizer() as opt:
            return not opt.is_finished

    @check_workchain_step
    def launch_calculations(self):
        self.report('Launching pending calculations.')
        with self.optimizer() as opt:
            calcs = {}
            for idx, inputs in opt.create_inputs().items():
                calcs[self._CALC_PREFIX + str(idx)] = submit(
                    self.get_deserialized_input('calculation_workchain'),
                    **inputs
                )
            self.report('Launching calculation {}'.format(idx))
        return ToContext(**calcs)

    @check_workchain_step
    def get_results(self):
        self.report('Checking finished calculations.')
        with self.optimizer() as opt:
            context_keys = dir(self.ctx)
            step_keys = [
                key for key in context_keys
                if key.startswith(self._CALC_PREFIX)
            ]
            outputs = {}
            for key in step_keys:
                idx = int(key.split(self._CALC_PREFIX)[1])
                self.report('Retrieving output for calculation {}'.format(idx))
                outputs[idx] = self.ctx[key].get_outputs_dict()
                delattr(self.ctx, key)
            opt.update(outputs)

    def finalize(self):
        self.report('Finalizing optimization procedure.')
        with self.optimizer() as opt:
            self.out('result', opt.result)