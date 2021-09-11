import re
import math
import sys
import gzip
import subprocess
import argparse

fig_count = 0

def tsplib_instance(path):
    with gzip.open(path) if path.endswith('.gz') else open(path) as f:
        content = f.readlines()
    data_line_pattern = re.compile(r'^\s*\d.*$')
    coord_pattern = re.compile(r'(?<=\d)\s+-?\d+(\.\d+)?(e\+\d\d)?\s+-?\d+(\.\d+)?(e\+\d\d)?')
    instance = [coord_pattern.search(line.decode('utf8')).group(0) for line in content[:-1] 
                if data_line_pattern.match(line.decode('utf8'))]
    instance = [' '.join(list(map(str, map(float, filter(lambda s: s != '', line.split(' ')))))) 
                for line in instance]
    return instance


def tsplib_solution(path):
    with gzip.open(path) if path.endswith('.gz') else open(path) as f:
        content = f.readlines()
    data_line_pattern = re.compile(r'^\s*\d')
    solution = [str(int(line.decode('utf8')) - 1) for line in content
                if data_line_pattern.match(line.decode('utf8'))]
    return solution


def run_solver(solver_path, instance):
    solver_input = (f'{len(instance)}\n' + '\n'.join(instance)).encode()
    print('Running solver...', end='')
    cproc = subprocess.run(solver_path, input=solver_input, stdout=subprocess.PIPE, check=True)
    print(' Done!')
    solution = cproc.stdout.decode('utf8').strip().split('\n')
    return instance, solution


def tour_length(instance, solution):
    def distance(vertex, other):
        return round(math.sqrt((vertex[0] - other[0])**2 + (vertex[1] - other[1])**2))

    coords = [tuple(map(float, line.split(' '))) for line in instance]
    tour = [coords[int(i)] for i in solution]
    tour.append(tour[0])
    return sum(distance(prev, next) for prev, next in zip(tour, tour[1:]))


def plot_tour(instance, solution, name):
    coords = np.array([tuple(map(float, line.split(' '))) for line in instance])
    tour = [coords[int(i)] for i in solution]
    tour.append(tour[0])  # Connect the tour

    global fig_count
    fig = plt.figure(fig_count)
    fig_count += 1

    for prev, next in zip(tour, tour[1:]):
        plt.plot((prev[0], next[0]), (prev[1], next[1]), 'k-', linewidth=.7)
    plt.scatter(coords[:,0], coords[:,1], zorder=len(tour), marker='.')
    plt.title(f'{name} (length = {tour_length(instance, solution)})')
    plt.xlabel('x')
    plt.ylabel('y')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Convert .tsp instances from TSPLIB to Kattis "tsp" instances.' 
                    'Note that not all TSPLIB instances are supported.')
    parser.add_argument('solver', help='An executable which solves the Kattis problem "tsp".')
    parser.add_argument('instance', help='A TSPLIB .tsp instance.')
    parser.add_argument('-o', '--optimal', help='An .opt.tour file corresponding to the instance.')
    parser.add_argument('-s', '--show', help='Show matplotlib visualizations.', action='store_true')
    parser.add_argument('-p', '--print', 
        help="Print a comparison between the solver's solution and the optimal solution. "
        "If no optimal solution is provided, this argument is ignored.", action="store_true")

    args = parser.parse_args()

    try:
        instance = tsplib_instance(args.instance)
    except AttributeError as e:
        print("Could not parse the .tsp file. (Not a supported instance)", file=sys.stderr)
        sys.exit(1)

    try:
        instance, solution = run_solver(args.solver, instance)
    except subprocess.CalledProcessError:
        print("Solver did not manage to run the parsed instance", file=sys.stderr)
        sys.exit(1)

    if args.optimal:
        try:
            optimal_solution = tsplib_solution(args.optimal)
            if len(optimal_solution) != len(solution):
                print("The solutions do not match. Something is either not matching," 
                    "not supported or the solver is faulty.", file=sys.stderr)
            if args.print:
                print('\nTours:')
                print(' sol  opt')
                for solver, optimal in zip(solution, optimal_solution):
                    print(f'{int(solver):4d} {int(optimal):4d}')
                print('\nLengths:')
                print('sol', tour_length(instance, solution))
                print('opt', tour_length(instance, optimal_solution))
        except AttributeError:
            print("Could not parse the .opt.tour file. (Not a supported instance)", 
                file=sys.stderr)

    if args.show:
        import numpy as np
        import matplotlib.pyplot as plt
        print("\nGenerating plots...", end='')
        plot_tour(instance, solution, 'Solver')
        if args.optimal and optimal_solution:
            plot_tour(instance, optimal_solution, 'Optimal')
        print(" Done!")
        plt.show()
