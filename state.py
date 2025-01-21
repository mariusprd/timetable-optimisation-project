from functools import reduce
import math as m
import random as r

from copy import deepcopy

from my_utils import *
from utils import *
import random

HARD_QUOTIENTS = {
    'c_intervals': 200,
    'c_stud_left': 40,
    'c_mult': 150
}
SOFT_QUOTIENT = 1

class State:
    '''
        Class that represents a state in the search space
    '''
    CLASSROOMS = None
    SUBJECTS = None
    PROF_SUBS = None
    CONSTRAINTS = None
    INPUT_FILE = None

    __specs = None # the specs of the timetable -> directly from the input file
    __min_capacity_of_classroom = None # the minimum capacity of a classroom
    __sorted_subjects = None # subjects sorted by number of classrooms where they can be taught


    def __init__(
            self,
            timetable: dict = None, # timetable: {day: {interval: {classroom: (professor, subject)}}} -> the timetable of the state
            profs: dict = None, # profs: {professor: list(day, interval)} -> intervals that the professor is already busy in a course
            students: dict = None, # students: {subject: int} -> number of students assigned to a subject at a certain time
            fitness: dict = None, # fitness: {c_intervals: int, c_stud_left: int, c_mult: int, c_soft: int, c_pause: int} -> the fitness of the state
            depth: int = 0 # depth of the state (only used for MCTS )
    ) -> None:
        
        if State.CLASSROOMS is None or State.SUBJECTS is None or State.CONSTRAINTS is None:
            if State.INPUT_FILE is None:
                raise ValueError("Environment unknown. Please set the input file first.")
            State.__set_env(State.INPUT_FILE, debug_flag=True)
        
        (self.timetable, self.profs) = (timetable, profs) if timetable is not None else State.__generate_timetable()
        self.students = students if students is not None else {subject: 0 for subject in State.SUBJECTS}
        self.fitness = self.__compute_fitness() if fitness is None else fitness
        self.depth = depth


    def apply_move(self, day: str, interval: tuple, classroom: str, prof: str, subject: str, depth: int = 0):
        '''
            Applies a move to the timetable
        '''
        new_timetable = deepcopy(self.timetable)
        new_profs = deepcopy(self.profs)
        new_students = deepcopy(self.students)
        new_fitness = deepcopy(self.fitness)

        # if move == remove old class
        if prof is None and subject is None and self.timetable[day][interval][classroom] is not None:
            old_prof, old_sub = self.timetable[day][interval][classroom]

            new_timetable[day][interval][classroom] = None
            new_profs[old_prof].remove((day, interval))

            if len(new_profs[old_prof]) >= 7:
                new_fitness['c_intervals'] -= HARD_QUOTIENTS['c_intervals']

            new_students[old_sub] -= State.CLASSROOMS[classroom][CAPACITATE]
            if new_students[old_sub] < State.SUBJECTS[old_sub][NUM_STUDENTS]:
                new_fitness['c_stud_left'] = State.__compute_c_stud_left(new_students)

            # if prof is in multiple places at the same time
            old_num_apps = reduce(lambda acc, x: acc + 1 if x == (day, interval) else acc, self.profs[old_prof], 0)
            if old_num_apps > 1:
                new_fitness['c_mult'] -= HARD_QUOTIENTS['c_mult']

            # update soft constraints
            if day in State.CONSTRAINTS[old_prof][DAY_CONSTRAINTS]:
                new_fitness['c_soft'] -= SOFT_QUOTIENT
            if interval in State.CONSTRAINTS[old_prof][INT_CONSTRAINTS]:
                new_fitness['c_soft'] -= SOFT_QUOTIENT

            # update the pause constraint
            new_fitness['c_pause'] = State.__compute_c_pause(new_timetable, new_profs)

        # if move == add new class (before the class was None) -> written by copilot (could be wrong)
        elif prof is not None and subject is not None and self.timetable[day][interval][classroom] is None:
            new_timetable[day][interval][classroom] = (prof, subject)
            new_profs[prof].append((day, interval))

            if len(new_profs[prof]) > 7:
                new_fitness['c_intervals'] += HARD_QUOTIENTS['c_intervals']

            new_students[subject] += State.CLASSROOMS[classroom][CAPACITATE]
            new_fitness['c_stud_left'] = State.__compute_c_stud_left(new_students)

            # if prof is in multiple places at the same time
            old_num_apps = reduce(lambda acc, x: acc + 1 if x == (day, interval) else acc, self.profs[prof], 0)
            if old_num_apps > 0:
                new_fitness['c_mult'] += HARD_QUOTIENTS['c_mult']
            
            # update soft constraints
            if day in State.CONSTRAINTS[prof][DAY_CONSTRAINTS]:
                new_fitness['c_soft'] += SOFT_QUOTIENT
            if interval in State.CONSTRAINTS[prof][INT_CONSTRAINTS]:
                new_fitness['c_soft'] += SOFT_QUOTIENT

            # update the pause constraint
            new_fitness['c_pause'] = State.__compute_c_pause(new_timetable, new_profs)

        # if move == change class -> remove class and add new class
        elif prof is not None and subject is not None and self.timetable[day][interval][classroom] is not None:
            _tmp_state = self.apply_move(day, interval, classroom, prof=None, subject=None)
            return _tmp_state.apply_move(day, interval, classroom, prof=prof, subject=subject, depth=depth)
        
        return State(new_timetable, new_profs, new_students, new_fitness, depth= depth)
    

    def get_next_states_hc(self):
        '''
            Lazily generates the next states of the current state (add/remove moves)
        '''
        for day in shuffle_dict(self.timetable).keys():
            for interval in shuffle_dict(self.timetable[day]).keys():
                for classroom in shuffle_dict(self.timetable[day][interval]).keys():

                    # if a class is already assigned to the classroom -> skip with a probability of 0.5
                    if self.timetable[day][interval][classroom] is not None and r.random() < 0.5:
                        continue

                    for subject in State.__sorted_subjects:
                        # don t add a class if there are no students left for that subject
                        if self.students[subject] >= State.SUBJECTS[subject][NUM_STUDENTS]:
                            continue

                        # if the classroom is not for this subject -> skip
                        if subject not in State.CLASSROOMS[classroom][MATERII]:
                            continue

                        sorted_profs = State.SUBJECTS[subject][PROF_FOR_SUBJECT]
                        random.shuffle(sorted_profs)
                        for prof in sorted_profs:
                            # if the professor is already busy in that interval -> skip
                            if (day, interval) in self.profs[prof]:
                                continue

                            # duplicate class -> skip
                            if self.timetable[day][interval][classroom] == (prof, subject):
                                continue

                            next_state = self.apply_move(day, interval, classroom, prof=prof, subject=subject)
                            yield next_state


    def get_random_action(self):
        '''
            Generate a random action for the current state => used in mcts simulation
        '''
        for day in shuffle_dict(self.timetable).keys():
            for interval in shuffle_dict(self.timetable[day]).keys():
                for classroom in shuffle_dict(self.timetable[day][interval]).keys():
                    if self.timetable[day][interval][classroom] is not None and r.random() < 0.5:
                        continue

                    for subject in State.__sorted_subjects:
                        # if the classroom is not for this subject -> skip
                        if subject not in State.CLASSROOMS[classroom][MATERII]:
                            continue

                        # don t add a class if there are no students left for that subject
                        if self.students[subject] >= State.SUBJECTS[subject][NUM_STUDENTS]:
                            continue

                        profs = State.SUBJECTS[subject][PROF_FOR_SUBJECT]
                        random.shuffle(profs)
                        for prof in profs:
                            if day in State.CONSTRAINTS[prof][DAY_CONSTRAINTS] or interval in State.CONSTRAINTS[prof][INT_CONSTRAINTS] and r.random() < 0.9:
                                continue

                            # if the professor is already busy in that interval -> skip
                            if (day, interval) in self.profs[prof]:
                                continue

                            # if prof already has 7 classes -> skip
                            if len(self.profs[prof]) >= 7:
                                continue

                            action = (day, interval, classroom, prof, subject)
                            return action
        return None


    def get_available_actions(self):
        '''
            Generates the next states of the current state
        '''
        actions = []
        break_c_actions = 0
        for day in self.timetable.keys():
            for interval in self.timetable[day].keys():
                for classroom in self.timetable[day][interval].keys():
                    if self.timetable[day][interval][classroom] is not None:
                        continue

                    for subject in State.__sorted_subjects:
                        # if the classroom is not for this subject -> skip
                        if subject not in State.CLASSROOMS[classroom][MATERII]:
                            continue

                        # don t add a class if there are no students left for that subject
                        if self.students[subject] >= State.SUBJECTS[subject][NUM_STUDENTS] and self.timetable[day][interval][classroom] is None:
                            continue

                        profs = State.SUBJECTS[subject][PROF_FOR_SUBJECT]
                        for prof in profs:
                            if day in State.CONSTRAINTS[prof][DAY_CONSTRAINTS] or interval in State.CONSTRAINTS[prof][INT_CONSTRAINTS] and break_c_actions >= 3:
                                continue
                            else:
                                break_c_actions += 1

                            # if the professor is already busy in that interval -> skip
                            if (day, interval) in self.profs[prof]:
                                continue

                            # if prof already has 7 classes -> skip
                            if len(self.profs[prof]) >= 7:
                                continue

                            action = (day, interval, classroom, prof, subject)
                            actions.append(action)
        return actions


    def __compute_fitness(self):
        '''
            Returns the fitness of the current state
        '''
        _fitness = {}
        _fitness['c_intervals'] = State.__compute_c_intervals(self.profs)
        _fitness['c_stud_left'] = State.__compute_c_stud_left(self.students)
        _fitness['c_mult'] = State.__compute_c_mult(self.timetable)
        _fitness['c_soft'] = State.__compute_c_soft(self.profs)
        _fitness['c_pause'] = State.__compute_c_pause(self.timetable, self.profs)

        return _fitness


    @staticmethod
    def __compute_c_intervals(profs: dict) -> int:
        '''
            Computes the fitness for the c_intervals constraint (professors teaching more than 7 classes per week)
        '''
        c_intervals = 0
        for _, i in profs.items():
            dif = max(0, len(i) - 7)
            c_intervals += dif * HARD_QUOTIENTS['c_intervals']
        return c_intervals
    

    @staticmethod
    def __compute_c_stud_left(students: dict):
        '''
            Computes the fitness for the c_stud_left constraint (number of students left for each subject)
        '''
        c_stud_left = 0
        for subject, no_students in students.items():
            dif = State.SUBJECTS[subject][NUM_STUDENTS] - no_students
            dif = max(0, m.ceil(dif / State.__min_capacity_of_classroom))
            c_stud_left += dif * HARD_QUOTIENTS['c_stud_left']

        return c_stud_left
    

    @staticmethod
    def __compute_c_mult(timetable: dict) -> int:
        '''
            Computes the fitness for the c_mult constraint (professor in multiple places at the same time)
        '''
        c_mult = 0
        for day in timetable:
            for interval in timetable[day]:
                profs_teaching = set()
                for classroom in timetable[day][interval]:
                    if timetable[day][interval][classroom] is not None:
                        prof, _ = timetable[day][interval][classroom]
                        if prof in profs_teaching:
                            c_mult += 100
                        profs_teaching.add(prof)
        return c_mult


    def soft_wrapper(self):
        '''
            Wrapper for the soft constraints
        '''
        print('*' * 50 + "SOFT CONSTRAINTS" + '*' * 50)
        return (State.__compute_c_soft(self.profs, debug_flag=True)
                + State.__compute_c_pause(self.timetable, self.profs, debug_flag=True))


    @staticmethod
    def __compute_c_soft(profs: dict, *, debug_flag: bool = False) -> int:
        '''
            Computes the fitness for the c_soft constraint (soft constraints)
        '''
        c_soft = 0

        for p in profs:
            if debug_flag:
                print(f"PROF: {p} that can teach {State.PROF_SUBS[p]}")
            
            # get the days that the professor is busy
            days_for_prof = set([d for d, _ in profs[p]])
            for d in days_for_prof:
                if d in State.CONSTRAINTS[p][DAY_CONSTRAINTS]:
                    c_soft += SOFT_QUOTIENT
                    if debug_flag:
                        print(f"\t!{d} -> NOT satisfied")
                else:
                    if debug_flag:
                        print(f"\t!{d} -> satisfied")

            # get the intervals that the professor is busy
            intervals_for_prof = set([i for _, i in profs[p]])
            for i in intervals_for_prof:
                if i in State.CONSTRAINTS[p][INT_CONSTRAINTS]:
                    c_soft += SOFT_QUOTIENT
                    if debug_flag:
                        print(f"\t!{i} -> NOT satisfied")
                else:
                    if debug_flag:
                        print(f"\t!{i} -> satisfied")

        return c_soft
    

    @staticmethod
    def __compute_c_pause(timetable: dict, profs: dict, *, debug_flag: bool = False) -> int:
        '''
            Computes the fitness for the c_pause constraint (professor has a pause of 2 hours between classes)
        '''
        if debug_flag:
            print("*" * 50 + " PAUSE CONSTRAINT " + "*" * 50)

        c_pause = 0
        for prof in profs:
            if State.CONSTRAINTS[prof][PAUSE] is None:
                continue
            
            if debug_flag:
                print(f"PROF: {prof} that can teach {State.PROF_SUBS[prof]}")
            
            all_good_debug = True
            for day in timetable.keys():
                prof_classes = [i for d, i in profs[prof] if d == day]
                if len(prof_classes) < 2:
                    continue

                max_pause = 0
                prof_classes.sort(key=lambda x: x[1])
                for i in range(1, len(prof_classes)):
                    cur_pause = prof_classes[i][1] - prof_classes[i - 1][1]
                    max_pause = max(max_pause, cur_pause)

                max_pause -= 2
                if max_pause > State.CONSTRAINTS[prof][PAUSE]:
                    all_good_debug = False
                    if debug_flag:
                        print(f"\t!Pauza>{State.CONSTRAINTS[prof][PAUSE]} -> NOT satisfied on day {day}: {max_pause}")

                c_pause += max((max_pause - State.CONSTRAINTS[prof][PAUSE]), 0) * SOFT_QUOTIENT

            if debug_flag and all_good_debug:
                print(f"\t!Pauza>{State.CONSTRAINTS[prof][PAUSE]} -> satisfied")

        return c_pause


    def is_final(self) -> bool:
        '''
            Returns True if the state is final
        '''
        return self.total_fitness() == 0
    

    def total_fitness(self) -> float:
        '''
            Returns the total fitness of the state
        '''
        return sum(self.fitness.values())


    def total_fitness_mcts(self) -> tuple:
        '''
            Returns the total fitness of the state for the MCTS algorithm
        '''
        hard = (
                self.fitness['c_intervals'] / HARD_QUOTIENTS['c_intervals'] +
                self.fitness['c_stud_left'] / HARD_QUOTIENTS['c_stud_left'] +
                self.fitness['c_mult'] / HARD_QUOTIENTS['c_mult']
            )
        
        soft = (
                self.fitness['c_soft'] +
                self.fitness['c_pause']
            )

        return int(hard), soft


    @staticmethod
    def get_bfactor() -> int:
        '''
            Returns the avg branching factor (int)
        '''
        bfactor = 1
        bfactor *= len(State.__specs[ZILE])
        bfactor *= len(State.__specs[INTERVALE])
        bfactor *= len(State.__specs[SALI])

        # avg number of classes per subject
        avg_class_per_sub = sum([len(State.SUBJECTS[sub][CLASS_FOR_SUBJECT]) for sub in State.SUBJECTS]) / len(State.SUBJECTS)
        bfactor *= avg_class_per_sub

        # avg number of professors per subject
        avg_prof_per_sub = sum([len(State.SUBJECTS[sub][PROF_FOR_SUBJECT]) for sub in State.SUBJECTS]) / len(State.SUBJECTS)
        bfactor *= avg_prof_per_sub

        return round(bfactor)


    @staticmethod
    def __set_env(input_file: str, debug_flag: bool = False):
        '''
            Sets the environment for the search space
        '''
        timetable_specs = read_yaml_file(input_file)

        State.CLASSROOMS = timetable_specs[SALI]
        State.SUBJECTS = subject_prof_class(timetable_specs[MATERII], timetable_specs[PROFESORI], timetable_specs[SALI])
        State.PROF_SUBS = {prof: timetable_specs[PROFESORI][prof][MATERII] for prof in timetable_specs[PROFESORI]}
        State.CONSTRAINTS = get_constraints(timetable_specs[PROFESORI])
        
        State.__specs = timetable_specs
        State.__min_capacity_of_classroom = min(State.CLASSROOMS.values(), key=lambda x: x[CAPACITATE])[CAPACITATE]
        State.__sorted_subjects = sorted(State.SUBJECTS.keys(), key=lambda x: len(State.SUBJECTS[x][CLASS_FOR_SUBJECT]))

        if debug_flag:
            print("%" * 70 + " ENVIRONMENT " + "%" * 70)
            print(f"\nClassrooms: {State.CLASSROOMS}")
            print(f"\nSubjects: {State.SUBJECTS}")
            print(f"\nProfessors: {State.PROF_SUBS}")
            print(f"\nConstraints: {State.CONSTRAINTS}")
            print("\n" + "%" * 152 + "\n")


    @staticmethod
    def __generate_timetable():
        '''
            Generates the initial state (empty state)
        '''
        empty_timetable = {day: {eval(interval): {classroom: None for classroom in State.__specs[SALI].keys()} for interval in State.__specs[INTERVALE]} for day in State.__specs[ZILE]}
        empty_profs = {prof: [] for prof in State.CONSTRAINTS.keys()}
        return empty_timetable, empty_profs
    

    def clone(self):
        '''
            Returns a clone of the current state
        '''
        return State(deepcopy(self.timetable), deepcopy(self.profs), deepcopy(self.students), deepcopy(self.fitness), depth=self.depth)


    def __str__(self):
        '''
            Returns a string representation of the state
        '''
        timetable_str = f"\n\n{pretty_print_timetable(self.timetable, State.INPUT_FILE)}"
        fitness_str = ''
        # fitness_str = f"{'#' * 50} FITNESS: {self.fitness} {'#' * 50}\n\n"

        return timetable_str + fitness_str
