from math import sqrt, log
from random import choice
from state import State

class Node:
    def __init__(self, state, parent=None) -> None:
        self.state = state
        self.parent = parent
        self.actions = {} # dict of actions -> Node (child nodes)
        self.quality = 0
        self.visits = 0

    def __str__(self) -> str:
        return f"Visits: {self.visits} <--> Quality: {self.quality:.4f} | num_children: {len(self.actions)}"


def print_tree(tree: Node, indent=0):
    '''
        Prints the tree
    '''
    if not tree:
        return
    
    tab = ' ' * indent
    print(f"{tab}{tree}")
    for action in tree.actions.keys():
        print(f"{tab}action: {action}")
        print_tree(tree.actions[action], indent + 3)


def compute_reward(state: State):
    '''
        Computes the reward for a state
    '''
    hard, soft = state.total_fitness_mcts()

    if hard > 0:
        return 0.0
    
    if soft == 0:
        return 50
    
    reward = 20 / (1 + soft)
    return reward


def compute_max_depth(state: State):
    '''
        Computes the maximum depth of the tree
    '''
    depth = 1
    depth *= len(state.timetable.keys())
    depth *= len(state.timetable['Luni'].keys())
    depth *= len(state.timetable['Luni'][(8, 10)].keys())
    return depth


def is_final(state: State):
    '''
        Returns True if the state is final, False otherwise
    '''
    return state.is_final() or state.depth >= MAX_DEPTH


CP = 1.0 / sqrt(2.0)
def uct(Q_a, N_a, N_node, c=CP):
    '''
        UCT formula
    '''
    return Q_a / N_a + c * sqrt(2 * log(N_node) / N_a)


def select_action(node, c=CP):
    '''
        Selects the action with the highest UCT value

        Q_a - quality of the child node
        N_a - number of visits of the child node
        N_node - number of visits of the current node
        c - exploration parameter
    '''
    if not node.actions:
        return None
    return max(node.actions.keys(), key=lambda action: uct(node.actions[action].quality, node.actions[action].visits, node.visits, c=c))


def mcts(state0: State, budget: int, tree: Node):
    '''
        MCTS algorithm
        Params:
            state0: initial state
            budget: number of iterations
            tree: the tree to use
    '''
    # if there is a tree, use it
    if tree:
        root = tree
        root.parent = None # forget the parent -> less calculations for backpropagation
    else:
        root = Node(state0)

    num_states = 0

    for i in range(budget):
        node = root

        # Selection => find a leaf node
        while not is_final(node.state) and all(act in node.actions for act in node.state.get_available_actions()):
            action = select_action(node)
            # this is for depth too small
            if action is None:
                break
            node = node.actions[action]


        # Expansion => expand the leaf node
        available_actions = node.state.get_available_actions()
        if not is_final(node.state) and not all(act in node.actions for act in available_actions):
            possible_actions = [a for a in available_actions if a not in node.actions]
            action = choice(possible_actions)

            new_state = node.state.apply_move(*action, depth=node.state.depth + 1)
            num_states += 1
            node.actions[action] = Node(new_state, parent=node)

            node = node.actions[action]


        # Simulation => simulate a game from the current state
        state = node.state
        while not is_final(state):
            action = state.get_random_action()
            if not action:
                break
            state = state.apply_move(*action, depth=state.depth + 1)
            num_states += 1


        # Backpropagation => update the quality and visits of the nodes
        reward = compute_reward(state)
        while node:
            node.visits += 1
            node.quality += reward
            node = node.parent


    final_action = select_action(root, c=0.0)
    if final_action is None:
        return None, None, num_states
    return final_action, root.actions[final_action], num_states


def run_mcts(state: State, debug_flag=False):
    '''
        Runs the MCTS algorithm
    '''
    BUDGET = 50

    global MAX_DEPTH
    MAX_DEPTH = compute_max_depth(state)

    iters, num_states = 0, 0

    state = state.clone()
    tree = None

    while state and not is_final(state):
        iters += 1
        action, tree, cur_num_states = mcts(state, BUDGET, tree)
        num_states += cur_num_states
        if action is None:
            break

        if debug_flag:
            print(f"\nApplying action: {action} -> depth: {state.depth}")
            print(f"Fitness: {state.total_fitness_mcts()}\n")

        state = state.apply_move(*action, depth=state.depth + 1)

    if debug_flag:
        print(f"Final state: {state}")

    return state.is_final(), iters, num_states, state
