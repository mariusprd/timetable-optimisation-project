import os, sys

from datetime import datetime
from time import time
from utils import *
from state import State, HARD_QUOTIENTS

from hill_climb import hill_climbing_random_restart, hill_climbing_first_X, hill_climbing
from mcts import run_mcts

VERSION = "final version"
N_TRIALS = 1


def run_test(algorithm: callable, input_file: str, n_trials: int, print_constraints: bool = False, **kwargs):
    ''' Run n_trials tests for the given algorithm and input file '''
    wins, fails = 0, 0
    end_fitness = [0 for _ in range(n_trials)]
    total_states = 0


    # set the environment
    State.INPUT_FILE = input_file

    best_state = None
    best_fitness = float('inf')

    for trial in range(n_trials):
        initial = State()
        is_final, iters, num_states, final_state = algorithm(initial, **kwargs)

        total_states += num_states

        if is_final:
            wins += 1
        else:
            fails += 1
            end_fitness[trial] = final_state.total_fitness()

        if final_state.total_fitness() < best_fitness:
            best_state = final_state
            best_fitness = final_state.total_fitness()

        print('*' * 120)
        print(f"Trial {trial + 1} | {'W' if is_final else 'L'} | ITERS {iters} | NUM_STATES {num_states} | FITNESS {end_fitness[trial]}")
        print(final_state)


    # log the results
    with open("results_timeline", 'a') as file:
        print(f"-- {datetime.now()} --", file=file)
        print(f"version: {VERSION}", file=file)
        print(f"params: {HARD_QUOTIENTS}", file=file)
        print(f"num_trials: {n_trials}", file=file)
        print(f"file: {input_file} | alg: {ALGORITHM} | W: {wins} | L: {fails} | avg_fit: {sum(end_fitness) / n_trials:.2f} | best_fit: {best_fitness}\n", file=file)

    # write the best state to a file
    out_file = f"outputs/{input_file.split('/')[-1]}".split('.')[0] + ".txt"
    print(f"Writing best state to {out_file}...")
    with open(out_file, 'w') as file:
        print(pretty_print_timetable(best_state.timetable, INPUT_FILE), file=file)

    if print_constraints:
        print(f"Soft constraints: {best_state.soft_wrapper()}")

    print(f"\n\nWins: {wins} | Fails: {fails}")
    print(f"Win percentage: {wins / n_trials * 100:.2f}")
    print(f"Average number of states explored: {total_states / n_trials:.2f}")
    print(f"Average end fitness(normalized): {sum(end_fitness) / n_trials:.2f}")
    print(f"Best state has fitness(normalized) {best_fitness}")


if __name__ == '__main__':
    # receive a string and an input file
    if len(sys.argv) < 2 or len(sys.argv) > 4:
        print("\t!!! Usage: python3 orar.py <algorithm> <input_file> [n_trials]")
        sys.exit(1)

    if len(sys.argv) == 4:
        N_TRIALS = int(sys.argv[3])

    ALGORITHM = sys.argv[1]
    INPUT_FILE = sys.argv[2]

    # check if the algorithm_name is valid
    if ALGORITHM == 'hc':
        algorithm = hill_climbing_random_restart
    elif ALGORITHM == 'hc_first':
        algorithm = hill_climbing_first_X
    elif ALGORITHM == 'hc_classic':
        algorithm = hill_climbing
    elif ALGORITHM == 'mcts':
        algorithm = run_mcts
    else:
        print("Invalid algorithm => Options are: hc [or hc_first or hc_classic], mcts")
        sys.exit(1)

    # create outputs dir if it doesn't exist
    if not os.path.exists("outputs"):
        os.makedirs("outputs")

    # run the test and time it
    time_start = time()
    run_test(algorithm, INPUT_FILE, n_trials=N_TRIALS)
    time_end = time()

    print(f"\nExecution time: {(time_end - time_start):.2f} seconds")
