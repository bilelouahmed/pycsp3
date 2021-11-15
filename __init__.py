import atexit
import os
import sys

from collections import namedtuple
from itertools import product, permutations

__python_version__ = str(sys.version).split(os.linesep)[0].split(' ')[0]
__pycsp3_version__ = open(os.path.join(os.path.dirname(__file__), 'version.txt'), encoding='utf-8').read()

if sys.version_info[0] < 3 or sys.version_info[1] < 6:
    raise Exception(os.linesep + " Python should be at least 3.6" + os.linesep + " Your version is Python " + __python_version__)

from pycsp3.functions import variant, subvariant, Var, VarArray, satisfy, minimize, maximize, annotate
from pycsp3.functions import And, Or, Not, Xor, IfThen, IfThenElse, Iff, Slide
from pycsp3.functions import protect, col, abs, min, max, xor, iff, imply, ift, expr, conjunction, disjunction
from pycsp3.functions import (AllDifferent, AllDifferentList, AllEqual, Increasing, Decreasing, LexIncreasing, LexDecreasing, Sum, Count, NValues, Cardinality,
                              Maximum, Minimum, Channel, NoOverlap, Cumulative, BinPacking, Circuit, Clause)
from pycsp3.functions import posted, objective, unpost, value, values

from pycsp3.tools.curser import columns, diagonal_down, diagonals_down, diagonal_up, diagonals_up, cp_array
from pycsp3.tools.utilities import ANY, combinations, different_values, flatten, alphabet_positions, all_primes, integer_scaling, to_ordinary_table

from pycsp3.classes.auxiliary.conditions import lt, le, ge, gt, eq, ne, complement
from pycsp3.classes.auxiliary.ptypes import TypeStatus, TypeSolver
from pycsp3.classes.entities import clear
from pycsp3.classes.auxiliary.structures import Automaton, MDD  # KEEP it here after other imports

from pycsp3.compiler import default_data, load_json_data

UNSAT = TypeStatus.UNSAT
""" Solver status: unsatisfiable (means that no solution is found by the solver) """

SAT = TypeStatus.SAT
""" Solver status: satisfiable (means that at least one solution is found by the solver) """

OPTIMUM = TypeStatus.OPTIMUM
""" Solver status: optimum (means that an optimal solution is found by the solver) """

CORE = TypeStatus.CORE
""" Solver status: core (means that an unsatisfiable core has been extracted by the solver) """

UNKNOWN = TypeStatus.UNKNOWN
""" Solver status: unknown (means that the solver is unable to solve the problem instance)  """

ACE = TypeSolver.ACE
""" Solver ACE (AbsCon Essence) """

CHOCO = TypeSolver.CHOCO
""" Solver Choco """

ALL = "all"
""" Constant used to indicate that all solutions must be sought """

if sys.argv:
    if len(sys.argv) == 1 and sys.argv[0] == "-m":  # copy of models
        import shutil
        import pycsp3

        print("Python version: ", __python_version__)
        print("PyCSP3 version: ", __pycsp3_version__)
        problems = os.sep.join(pycsp3.__file__.split(os.sep)[:-1]) + os.sep + "problems" + os.sep
        target = os.getcwd() + os.sep + "problems" + os.sep
        print("Source of files found: ", problems)
        shutil.copytree(problems, target, ignore=shutil.ignore_patterns('g6_testing', 'g7_todo', 'tests', '__init__.py', '__pycache__*'))
        print("Successfully created the directory " + target + " containing the problems !")
        exit(0)
    from pycsp3.compiler import Compilation

    if sys.argv[-1] == '-debug':  # debug mode
        try:
            Compilation.load()
            data = Compilation.data
            with open(sys.argv[0]) as f:
                code = compile(f.read(), sys.argv[0], 'exec')
                exec(code)
        except Exception as e:
            import traceback

            print("Error: ", e)
            # TODO analysing cases and displaying information (most modeling mistakes)
            print("\n")
            print(traceback.format_exc())
            exit(1)
    elif sys.argv[0] == '':  # console mode
        Compilation.load(console=True)
        data = None
    elif "pycsp3/problems/tests/" in sys.argv[0]:  # test mode
        # TODO is it correct (for avoiding compiling two times)?
        #  analysing if we have to compile (e..g, when running the tester, we should not try to do that);
        #  Trying to replace this with the inspector?
        Compilation.done = True
    else:
        Compilation.load()
        data = Compilation.data

_solver = None  # current solver


def _set_solver(name):
    global _solver
    if name == CHOCO:
        from pycsp3.solvers.choco import Choco
        _solver = Choco()
    else:  # Fallback case => ace
        from pycsp3.solvers.ace import Ace
        _solver = Ace()
    return _solver


def solver(name=None):
    """
    With no argument (name being None), the function returns the current solver (the last one that has been built).
    With an argument (name not being None), the function builds the solver whose name is specified, and returns it.

    :param name: the name of the solver to be built, or None (by default)
    :return: either the current solver if the specified name is None, or a newly created solver whose name is specified
    """
    return _solver if name is None else _set_solver(name)


def compile(filename=None, *, verbose=1):
    """
    Compiles the current model

    :param filename: the filename of the compiled problem instance
    :param verbose: verbosity level from -1 to 2
    :return: a pair composed of a string (filename) and a Boolean (True if a COP, False otherwise)
    """
    global _solver
    from pycsp3.compiler import Compilation
    from pycsp3.dashboard import options
    filename, cop = Compilation.compile(filename, verbose=verbose)
    solving = ACE.name if options.solve else options.solver
    if solving:
        if options.display:
            print("Warning: options -display and -solve should not be used together.")
            return filename
        from pycsp3.solvers.solver import process_options
        solver_name, args, args_recursive = process_options(solving)
        solver_name = next(ss for ss in TypeSolver if ss.name.lower() == solver_name.lower())
        _solver = _set_solver(solver_name)
        result = _solver.solve((filename, cop), solving, args, args_recursive, compiler=True, verbose=verbose, automatic=True)
        print("\nResult: ", result)
        if solution():
            print(solution())
    return filename, cop


def status():
    """
    Returns the status of the last solving operation, or None
    """
    return None if _solver is None else _solver.status


def solution():
    """
    Returns a complex object corresponding to the last found solution, or None
    """
    return None if _solver is None else _solver.last_solution


def n_solutions():
    """
    Returns the number of solutions found by the last solving operation, or None
    """
    return None if _solver is None else _solver.n_solutions


def bound():
    """
    Returns the bound found by the last solving operation, or None
    """
    return None if _solver is None else _solver.bound


def core():
    return None if _solver is None else _solver.core


def solve(*, solver=ACE, options="", filename=None, verbose=-1, sols=None, extraction=False):
    """
    Solves the current model (after compiling it) and returns the status of this operation.

    :param solver: name of the solver (ACE or CHOCO)
    :param options: specific options for the solver
    :param filename: the filename of the compiled problem instance
    :param verbose: verbosity level from -1 to 2
    :param sols: number of solutions to be found (ALL if no limit)
    :param extraction: True if an unsatisfiable core of constraints must be sought
    :return: the status of the solving operation
    """
    global _solver
    instance = compile(filename, verbose=verbose)
    if instance is None:
        print("Problem when compiling")
    else:
        _solver = _set_solver(solver)
        if solver == ACE:
            options += " -v=" + str(verbose)
            if sols == ALL or isinstance(sols, int) and sols > 1:
                options += " -xe -xc=false"
        _solver.setting(options)
        limit = "limit=no" if sols == ALL else "limit=" + str(sols) + "sols" if isinstance(sols, int) else ""
        return _solver.solve(instance, string_options=limit, dict_options=dict(), dict_simplified_options=dict(), verbose=verbose, extraction=extraction)


# def solve(*, solver=ACE, options=None, filename=None, disabling_opoverrider=False, verbose=0, sols=None):

def _pycharm_security():  # for avoiding that imports are removed when reformatting code
    _ = (namedtuple, product, permutations)


@atexit.register
def end():
    from pycsp3.tools.utilities import Error
    if not Compilation.done and not Error.errorOccurrence:
        Compilation.compile(disabling_opoverrider=True)
