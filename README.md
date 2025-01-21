# Timetable Optimization Project

This project solves a timetable scheduling problem using two algorithms: **Hill Climbing** and **Monte Carlo Tree Search (MCTS)**. The goal is to minimize constraint violations in the generated timetables. The algorithms are implemented in Python and tested against various inputs.

---

## **Features**

### **State Representation**
- **Timetable**: Represents the schedule as a nested dictionary structure.
- **Fitness**: Tracks violations of constraints with weighted penalties:
  - Hard constraints: Must not be violated (e.g., professor availability).
  - Soft constraints: Preferable conditions (e.g., preferred teaching hours).
- **Helpers**: Efficiently manage state transitions and fitness updates using:
  - `profs`: Tracks professors' schedules.
  - `students`: Tracks student assignment per subject.

### **Algorithms**

#### **Hill Climbing**
- Starts from an empty timetable and iteratively improves by applying the best possible move.
- Implements deterministic and probabilistic pruning to reduce state space.
- Uses random restarts to escape local minima.

#### **Monte Carlo Tree Search (MCTS)**
- Explores possible moves statistically by simulating random rollouts from each state.
- Implements reward functions and pruning to prioritize states with minimal constraint violations.

---

## **Project Structure**
```
.
├── check_constraints.py       # Utility to validate constraints in timetables
├── hill_climb.py              # Hill Climbing algorithm implementation
├── mcts.py                    # Monte Carlo Tree Search implementation
├── my_utils.py                # Additional utilities
├── orar.py                    # Main script for running the algorithms
├── state.py                   # State representation and manipulation
├── utils.py                   # General utility functions
├── inputs/                    # Input files (YAML format) defining problem scenarios
│   ├── dummy.yaml
│   ├── orar_bonus_exact.yaml
│   ├── orar_constrans_incalcat.yaml
│   ├── orar_mare_relaxat.yaml
│   ├── orar_mediu_relaxat.yaml
│   └── orar_mic_exact.yaml
├── outputs/                   # Outputs of the algorithms
│   ├── dummy.txt
│   ├── orar_bonus_exact.txt
│   ├── orar_constrans_incalcat.txt
│   ├── orar_mare_relaxat.txt
│   ├── orar_mediu_relaxat.txt
│   └── orar_mic_exact.txt
├── refs/                      # Reference outputs for validationtime
└── tema1_IA.pdf               # Detailed project description
```

---

## **Usage**

### **1. Setup**
Ensure you have Python 3 installed with the required libraries.


### **2. Run the Project**
To execute the program and generate timetables:
```bash
python3 orar.py <algorithm> <input_file> [n_trials]
```
- **`<algorithm>`**: Choose between `hill_climb` or `mcts`.
- **`<input_file>`**: Specify the path to a YAML input file (e.g., `inputs/orar_bonus_exact.yaml`).
- **`[n_trials]`** (optional): Number of trials for random restarts (default: 1).

### **3. Example**
Generate a timetable using the Hill Climbing algorithm:
```bash
python3 orar.py hill_climb inputs/orar_mediu_relaxat.yaml
```
Generate a timetable using the MCTS algorithm with 5 trials:
```bash
python3 orar.py mcts inputs/orar_constrans_incalcat.yaml 5
```

### **4. Outputs**
Results are saved in the `outputs/` directory, with filenames matching the input file. Logs of state transitions are stored in `results_timeline/`.

---

## **Constraints**

### **Hard Constraints**
- Professors cannot be scheduled in multiple classrooms at the same time.
- Classrooms must meet the minimum capacity requirements.
- A professor cannot teach more than 7 hours per week.

### **Soft Constraints**
- Respect professors' preferred days and times.
- Avoid scheduling gaps in professors' timetables.

---

## **Future Enhancements**
- Add support for dynamic adjustments of constraints and parameters.
- Implement advanced reward functions to improve MCTS performance.
- Visualize timetables for better understanding and analysis.
