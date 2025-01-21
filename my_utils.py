import yaml, random

from utils import MATERII


CAPACITATE = 'Capacitate'
NUM_STUDENTS = 'Number_of_students'
PROF_FOR_SUBJECT = 'Professors_for_subject'
CLASS_FOR_SUBJECT = 'Classrooms_for_subject'
CONSTRANGERI = 'Constrangeri'
DAY_CONSTRAINTS = 'Day_constraints'
INT_CONSTRAINTS = 'Interval_constraints'
PAUSE = 'Pauza'


def interval_to_tuple(interval: str) -> tuple:
    '''
        Transforms a string interval into a tuple of integers a-b -> (a, b)
    '''
    return tuple(map(int, interval.split('-')))


def interval_to_string(interval: tuple) -> str:
    '''
        Transforms a tuple of integers into a string interval
    '''
    return f"{interval[0]}-{interval[1]}"


def subject_prof_class(subjects: dict, professors: dict, classrooms: dict) -> dict:
    '''
        Returns a dict with keys the subjects and values a dict {
            'Number_of_students': number of students that take the subject,
            'Professors_for_subject': list of professors that can teach the subject
            'Classrooms_for_subject': list of classrooms where the subject can be taught
        } 
    '''
    res = {}
    for s in subjects.keys():
        res[s] = {}
        res[s][NUM_STUDENTS] = subjects[s]
        res[s][PROF_FOR_SUBJECT] = [p for p in professors.keys() if s in professors[p][MATERII]]
        res[s][CLASS_FOR_SUBJECT] = [c for c in classrooms.keys() if s in classrooms[c][MATERII]]
    return res


def break_constraints(profs: dict) -> dict:
    '''
        Returns profs but with broken interval constraints
    '''
    for p in profs.keys():
        constraints = profs[p][CONSTRANGERI]
        new_constraints = []
        for cons in constraints:
            positive = cons[0] != '!'
            cons = cons[1:] if not positive else cons

            if cons[0].isdigit():
                start, end = interval_to_tuple(cons)
                if end - start > 2:
                    for i in range(start, end, 2):
                        new_constraints.append(f"{'!' if not positive else ''}{interval_to_string((i, i + 2))}")
                else:
                    cons = '!' + cons if not positive else cons
                    new_constraints.append(cons)
            else:
                cons = '!' + cons if not positive else cons
                new_constraints.append(cons)
        profs[p][CONSTRANGERI] = new_constraints

    return profs


def get_constraints(profs: dict) -> dict:
    '''
        Returns a dict with the negative constraints of the professors
    '''

    constraints = {}
    for p in profs.keys():
        constraints[p] = {
            DAY_CONSTRAINTS: set(),
            INT_CONSTRAINTS: set(),
            PAUSE: None
        }

        for cons in profs[p][CONSTRANGERI]:
            if cons[0] != '!':
                continue
            else:
                cons = cons[1:]

            # interval constraint
            if cons[0].isdigit():
                start, end = interval_to_tuple(cons)
                if end - start > 2:
                    for i in range(start, end, 2):
                        constraints[p][INT_CONSTRAINTS].add((i, i + 2))
                else:
                    constraints[p][INT_CONSTRAINTS].add((start, end))
            # pause constraint (bonus)
            elif cons[0] == 'P':
                constraints[p][PAUSE] = int(cons[-1])
            # day constraint
            else:
                constraints[p][DAY_CONSTRAINTS].add(cons)

    return constraints


def pretty_print_dict(name: str, d: dict, marker: chr = '=') -> None:
    '''
        Pretty prints a dictionary
    '''
    print(f"\n{marker * 25}{name}{marker * 25}")
    print(yaml.dump(d, default_flow_style=False, indent=4))
    print(marker * (50 + len(name)))


def shuffle_dict(d: dict) -> dict:
    '''
        Shuffles the elements of a dictionary
    '''
    elems = list(d.items())
    random.shuffle(elems)
    return dict(elems)
