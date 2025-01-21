import math as m

from state import State


def hill_climbing_first_X(initial: State, max_iters: int = 200, *, X: int = 50):
    '''
        Hill climbing algorithm that chooses the best X states from the better states -> faster than the normal hill climbing, but less accurate
        Reference values for X:
            - ~100 for orar_bonus
            - ~500 for orar_mare
            - ~100 for orar_mediu
            - ~50 for orar_mic
            - ~10 for dummy
    '''
    iters, num_states = 0, 0
    state = initial.clone()

    while iters < max_iters:
        iters += 1

        cur_state = state

        better_states = []  # pair of (state, fitness)
        num_of_better_states = 0

        for next_state in cur_state.get_next_states_hc():
            num_states += 1
            if next_state.total_fitness() < cur_state.total_fitness():
                better_states.append((next_state, next_state.total_fitness()))
                num_of_better_states += 1
            
            if num_of_better_states == X:
                break

        if num_of_better_states > 0:
            state = min(better_states, key=lambda x: x[1])[0] # choose the best state from the first x better states
        else:
            break

    return state.is_final(), iters, num_states, state


def hill_climbing_random_restart(initial: State, max_iters: int = 200, max_restarts: int = 10, print_flag: bool = True):
    '''
        Hill climbing algorithm that restarts the search from a random state if the found state is not final
    '''

    def compute_start_X(bfactor: int) -> int:
        '''
            Computes the starting value for X based on the branching factor
        '''
        q = [
            7.8623791157809304e+000,
            7.0026630003745260e-002,
            -5.1206057797886388e-005,
            1.8778050205548963e-008,
            -3.3152162666652554e-012,
            2.7586335982464149e-016
        ]

        pol = q[0] + q[1] * bfactor + q[2] * bfactor**2 + q[3] * bfactor**3 + q[4] * bfactor**4 + q[5] * bfactor**5
        return round(pol)

    def compute_rise_factor(max_restarts: int) -> float:
        '''
            Computes the rise factor based on the number of restarts
        '''
        return m.pow(10, 1 / max_restarts)
    

    B = initial.get_bfactor()
    X = compute_start_X(B)
    R = compute_rise_factor(max_restarts)

    best_state = initial.clone()
    total_iters, total_states = 0, 0

    for i in range(max_restarts):
        is_final, iters, num_states, state = hill_climbing_first_X(initial, max_iters, X=X)
        total_iters += iters
        total_states += num_states

        if print_flag:
            print(f"\tFinished random restart {i + 1} / {max_restarts} [first {X} states] -> fitness: {state.total_fitness()}")

        if state.total_fitness() < best_state.total_fitness():
            best_state = state

        if is_final:
            return is_final, total_iters, total_states, state
        
        # increase X for the next restart
        X = round(X * R)
        
    return False, total_iters, total_states, best_state
        

def hill_climbing(initial: State, max_iters: int = 200):
    '''
        Classic hill climbing algorithm
    '''
    iters, num_states = 0, 0
    state = initial.clone()

    while iters < max_iters:
        iters += 1

        cur_state = state

        for next_state in cur_state.get_next_states_hc():
            num_states += 1
            if next_state.total_fitness() < cur_state.total_fitness():
                cur_state = next_state

        if cur_state == state:
            break

        state = cur_state

    return state.is_final(), iters, num_states, state
