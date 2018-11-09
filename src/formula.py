import random
import platform
import os
import re
import multiprocessing as mp
from collections.abc import Sequence
from src.utils import *


if platform.sys.version_info.major < 3:
    raise Exception("Must be Python 3")


if platform.sys.version_info.minor < 6:

    def choices(seq, weights = None):
        if not weights:
            weights = [1/len(seq) for _ in range(0,len(seq))]

        acc = 0
        dice = random.random()
        for p,x in zip(weights, seq):
            acc += p
            if acc > dice:
                return [x]

    random.choices = choices


class Formula:
    """ CNF formulae in DIMACS format """

    def __init__(self, dimacs = None, clauses = None, num_vars = None, sat_assignment = None):
        """ Load a formula from a .cnf (DIMACS) file """
        # check for argument validity
        if __debug__:
            type_check('dimacs', dimacs, str, optional = True)
            instance_check('clauses', clauses, Sequence, optional = True)
            type_check('num_vars', num_vars, int, optional = True)
            value_check('num_vars', num_vars, optional = True, positive = strict_positive)
            instance_check('sat_assignment', sat_assignment, Assignment, optional = True)

        # init variables
        self.clauses = []
        self.num_clauses = 0
        self.num_vars = 0
        self.comments = []
        self.occurrences = []
        self.max_clause_length = 0
        self.satisfying_assignment = None

        # parse the file.
        if dimacs:
            r = re.compile(r'-?\d+')           # find numbers
            rh = re.compile(r'-?0x[0-9a-fA-F]+') # find hex numbers

            for line in dimacs.splitlines():
                if line[0] == 'c':
                    if line.startswith('c assgn'):
                        hex_val, = rh.findall(line)
                    else:
                        self.comments.append(line)
                elif line[0] == 'p':
                    n, m = r.findall(line)
                    self.num_vars = int(n)
                    self.num_clauses = int(m)
                    self.satisfying_assignment = Assignment(int(hex_val,16), int(n))
                else:
                    self.clauses.append(list(map(int, r.findall(line)))[:-1])
                    if len(self.clauses[-1]) > self.max_clause_length:
                        self.max_clause_length = len(self.clauses[-1])

        # or use the given stuff
        elif not dimacs and clauses and num_vars and sat_assignment:
            self.satisfying_assignment = sat_assignment
            self.clauses = clauses
            self.num_clauses = len(clauses)
            self.num_vars = num_vars
            self.max_clause_length = max(map(len,clauses))

        else:
            raise ValueError(
                "Either 'dimacs' or 'clauses', 'num_vars' and 'sat_assignment' must be provided"
            )

        self.occurrences = [[] for _ in range(0,self.num_vars*2+1)];

        for clause_idx, clause in enumerate(self.clauses):
            for lit in clause:
                self.occurrences[self.num_vars + lit].append(clause_idx)

        self.max_occs = 0
        for occ in self.occurrences:
            if len(occ) > self.max_occs:
                self.max_occs = len(occ)

        self.ratio = self.num_clauses / self.num_vars


    def __eq__(self, formula):
        if not formula:
            return False
        else:
            return all([
                self.num_vars == formula.num_vars,
                self.clauses == formula.clauses,
                str(self.satisfying_assignment) == str(formula.satisfying_assignment)
            ])

    def __str__(self):
        """ Represent formula in DIMACS format """

        toReturn = ''

        for comment in self.comments:
            toReturn += comment
        toReturn += 'c assgn {}\n'.format(str(self.satisfying_assignment))
        toReturn += 'p cnf {} {}\n'.format(self.num_vars, self.num_clauses)
        for clause in self.clauses:
            for literal in clause:
                toReturn += '{} '.format(literal)
            toReturn += '0\n'

        return toReturn


    def is_satisfied_by(self, assignment):
        assert isinstance(assignment, Assignment), "assignment is no Assignment"

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
        assert type(literal) == int, "literal is no int"
        assert literal != 0, "literal == 0"

        return self.occurrences[self.num_vars + literal]


    def generate_satisfiable_formula(num_vars, ratio, clause_length = 3, seed=None):
        assert type(clause_length) == int, "clause_length is no int"
        assert clause_length > 0, "clause_length <= 0"
        assert type(num_vars) == int, "num_vars is no int"
        assert num_vars > 0, "num_vars <= 0"
        assert type(ratio) == float, "ratio is no float"
        assert ratio > 0, "ratio <= 0"
        assert clause_length == 3, 'Method \'generate_satisfiable_formula\' only implemented for 3CNF yet.'

        # optional arguments
        if seed:
            random.seed(seed)

        satisfying_assignment = Assignment.generate_random_assignment(
            num_vars,
            seed = seed
        )


        num_clauses = int(ratio * num_vars)
        clauses = []
        p={1: 0.191, 2: 0.118, 3: 0.073}
        for i in range(0, num_clauses + 1):
            variables = random.sample(range(1,num_vars+1), clause_length)

            acc = [[]]
            for var in variables:
                acc = list(map(lambda xs: [var] + xs, acc)) + list(map(lambda xs: [-var] + xs, acc))

            f = lambda lit: 1 if satisfying_assignment.is_true(lit) else 0
            cs, ws = [], []
            for clause in acc:
                x = sum(map(f,clause))
                if x > 0:
                    cs.append(clause)
                    ws.append(p[x])

            c, = random.choices(cs,weights=ws)
            clauses.append(c)

        formula = Formula(
            clauses = clauses,
            num_vars = num_vars,
            sat_assignment = satisfying_assignment
        )
        if not formula.is_satisfied_by(satisfying_assignment):
            raise RuntimeError('formula not satisfied')
        return formula


    def generate_formula_pool(
            directory,
            number,
            num_vars,
            ratio,
            clause_length = 3,
            seed = None,
            poolsize = 1,
            verbose = False):
        assert type(directory) == str, "directory is no str"
        assert type(number) == int, "number is no int"
        assert number > 0, "number <= 0"
        assert type(num_vars) == int, "num_vars is no int"
        assert num_vars > 0, "num_vars <= 0"
        assert type(ratio) == float, "ratio is no float"
        assert ratio > 0, "ratio <= 0"
        assert type(clause_length) == int, "clause_length is no int"
        assert clause_length > 0, "clause_length <= 0"

        if seed:
            random.seed(seed)

        try:
            os.mkdir(directory)
        except FileExistsError:
            pass

        with mp.Pool(processes = 3) as pool:
            future_formulae = []
            for _ in range(0,number):
                ff = pool.apply_async(
                    Formula.generate_satisfiable_formula,
                    (
                        num_vars,
                        ratio,
                        clause_length
                    )
                )
                future_formulae.append(ff)

            idx = 0
            for ff in future_formulae:
                f = ff.get()
                filename = 'n{}-r{:.2f}-k{}-{:016X}.cnf'.format(
                    num_vars,
                    ratio,
                    clause_length,
                    hash(f),
                )
                with open(os.path.join(directory,filename),'w') as target:
                    target.write(str(f))

                del future_formulae[idx]
                idx += 1

                if verbose:
                    print(
                        'File {} written.'.format(
                            os.path.join(directory,filename)
                        )
                    )



    def __hash__(self):
        return abs(
            hash(
                '{}{}{}{}{}'.format(
                    self.num_vars,
                    self.max_clause_length,
                    self.ratio,
                    str(self.satisfying_assignment),
                    id(self)
                )
            )
        )


class Assignment:
    """ Assignment modelled as an array of bits """

    def generate_random_assignment(num_vars, seed = None):
        """ Randomly generating a number between
        0 and 2^num_vars, converting it into an assignment,
        and returning it
        """
        if __debug__:
            type_check('num_vars',num_vars,int)
            value_check('num_vars',num_vars,strict_positive=strict_positive)

        if seed:
            random.seed(seed)

        return Assignment(
            random.randrange(0,pow(2,num_vars)),
            num_vars,
        )


    def atoms_from_integer(number):
        """ Takes a number and converts it into a list of booleans """
        atoms = []
        n = number
        while n > 0:
            atoms.append(n % 2 == 1)
            n //= 2
        return atoms


    def integer_from_atoms(atoms):
        """ Takes a list of booleans and converts it into a number """
        n = 0
        tmp = atoms.copy()
        while tmp:
            n *= 2
            n += 1 if tmp.pop() else 0

        return n


    def flip(self, var_index):
        """ Flips the variable with the index given """
        if __debug__:
            type_check('var_index',var_index,int)
            value_check('var_index',var_index,strict_positive=strict_positive)

        self.atoms[var_index-1] = not self.atoms[var_index-1]


    def get_value(self, var_index):
        """ Returns the assignment to the variable with the index given """
        if __debug__:
            type_check('var_index',var_index,int)
            value_check(
                'var_index',var_index,
                strict_positive = strict_positive,
                less_than_n = lambda x: x <= self.num_vars
            )

        return self.atoms[var_index-1]

    def __getitem__(self, var_index):
        return self.get_value(var_index)

    def __setitem__(self, var_index, value):
        self.atoms[var_index] = True if value else False

    def __delitem__(self, var_index):
        pass


    def is_true(self, literal):
        if __debug__:
            type_check('literal',literal,int)
            value_check('literal',literal,not_zero = not_equal_to(0))

        t = self.get_value(abs(literal))
        return t if literal > 0 else not t


    def __init__(self, number, num_vars):
        """ Generate an assignment from an integer """
        if __debug__:
            type_check('number',number,int)

        self.atoms = Assignment.atoms_from_integer(number)
        self.atoms += [False]*(num_vars-len(self.atoms))
        self.num_vars = num_vars


    def __str__(self):
        """ Converts the assignment to a hex literal with 0x prefix """
        return hex(Assignment.integer_from_atoms(self.atoms))


    def hamming_dist(self, assgn):
        if __debug__:
            instance_check('assgn',assgn,Assignment)
            value_check(
                'assgn',assgn,
                n_matches = lambda a: a.num_vars == self.num_vars
            )

        dist = 0
        for i in range(0,self.num_vars):
            dist += 1 if self[i] != assgn[i] else 0

        return dist