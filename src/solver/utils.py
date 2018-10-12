class Formula:
    """ CNF formulae in DIMACS format """

    def __init__(self, filepath):
        """ Load a formula from a .cnf (DIMACS) file """
        # check for argument validity
        if not type(filepath) == str:
            raise TypeError("Argument 'filepath' was no string.")

        if not filepath.endswith('.cnf'):
            raise ValueError(filepath + " is no .cnf file.")

        # init variables
        self.clauses = []
        self.num_clauses = 0
        self.num_vars = 0
        self.comments = []
        self.occurrences = []
        self.max_clause_length = 0

        # Parse the file.
        with open(filepath) as f:
            r = re.compile(r'-?\d+')  # find numbers
            rh = re.compile(r'-?[0-9a-fA-F]+') # find hex numbers

            for line in f:
                if line.startswith('c assgn'):
                    self.satisfying_assignment = int(rh.find(line),16)
                if line[0] == 'c':
                    self.comments.append(line)
                elif line[0] == 'p':
                    n, m = r.findall(line)
                    self.num_vars = int(n)
                    self.num_clauses = int(m)
                else:
                    self.clauses.append(list(map(int, r.findall(line)))[:-1])
                    if len(self.clauses[-1]) > self.max_clause_length:
                        self.max_clause_length = len(self.clauses[-1])

        for i in range(0, self.numVars*2+1):
            self.occurrences.append([])

        for idx in range(0, self.num_clauses):
            for literal in self.clauses[idx]:
                self.occurrences[self.numVars + literal].append(idx)

        self.max_occs = 0
        for occ in self.occurrences:
            if len(occ) > self.max_occs:
                self.max_occs = len(occ)

        self.ratio = self.num_clauses / self.num_vars
        self.is_init = True

    def __str__(self):
        """ Represent formula in DIMACS format """

        self.checkInit()

        toReturn = ''

        for comment in self.comments:
            toReturn += comment
        toReturn += 'p cnf {} {}\n'.format(self.num_vars, self.num_clauses)
        for clause in self.clauses:
            for literal in clause:
                toReturn += '{} '.format(literal)
            toReturn += '0\n'

        return toReturn

    def is_satisfied_by(self, assignment):
        if not isinstance(assignment, Assignment):
            raise TypeError('The given argument is no assignment.')

        for clause in self.clauses:
            true_clause = False
            for literal in clause:
                if assignment.is_true(literal):
                    true_clause = True
                    break
            if not true_clause:
                return False

        return True

    def get_occurrences(self, literal):
        return self.occurrences[self.num_vars + literal]

    def generate_satisfiable_formula(clause_length, num_vars, ratio):
        raise RuntimeError(
            'Method \'generate_satisfiable_formula\' not implemented yet.'
        )
