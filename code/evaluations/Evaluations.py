from evaluations.trace_logging.TraceLoggingEvaluator import TraceLoggingEvaluator

__author__ = 'Oliver Schranz <oliver.schranz@cispa.saarland>'


class Evaluations(object):
    # constant map of all evaluations available
    MAP = {TraceLoggingEvaluator.EVAL_ID: TraceLoggingEvaluator()}
