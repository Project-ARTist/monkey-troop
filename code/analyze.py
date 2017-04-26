from argparse import ArgumentParser
from sys import argv

from ReportWriter import ReportWriter
from evaluations.Evaluations import Evaluations
from utils.filesystem_config import FilesystemConfig


__author__ = 'Oliver Schranz <oliver.schranz@cispa.saarland>'


def create_parser() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument('evaluation',
                        metavar='<EVALUATION>',
                        action='store',
                        help='The evaluation for which the result will be analyzed.')

    parser.add_argument('task',
                        metavar='<TASK>',
                        action='store',
                        help='The analysis task that should be executed.')

    parser.add_argument('-o', '--out-folder',
                        action='store',
                        help='Output folder for, e.g., results.')

    return parser


def main() -> None:

    parser = create_parser()
    args = parser.parse_args()

    evaluation = args.evaluation
    task = args.task
    out_overwrite = args.out_folder

    print('eval: ' + evaluation)
    print('task: ' + task)
    print('out overwrite: ' + str(out_overwrite))

    fixed_fields_front = [ReportWriter.KEY_PKG, ReportWriter.KEY_CATS]
    fixed_fields_back = [ReportWriter.KEY_SUCC, ReportWriter.KEY_WORKER, ReportWriter.KEY_TIMESTAMP]

    if evaluation not in Evaluations.MAP.keys():
        print('Evaluation not found: ' + evaluation)
        exit(-1)
    evaluator = Evaluations.MAP[evaluation]

    # setup singleton
    fsm_args = dict()
    if out_overwrite is not None:
        fsm_args['out'] = out_overwrite
    FilesystemConfig(**fsm_args)

    analyzer = evaluator.get_analyzer(fixed_fields_front=fixed_fields_front,
                                      fixed_fields_back=fixed_fields_back)

    api = analyzer.get_command_api()
    for command, method in api.items():
        if command == task:
            method()
            exit(0)
    print('Command ' + task + ' not found for evaluation ' + evaluator.EVAL_ID)


if __name__ == '__main__':
    main()
