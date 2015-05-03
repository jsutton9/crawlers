import random
import math

rules = [["sine", 1], ["cosine", 1], ["tanh", 1], ["gaussian", 1], ["mean", 2], ["product", 2], ["ramp", 1], ["step", 1], ["spike", 1], ["inverse", 1]]
properties = ["axial_stiffness", "bending_stiffness", "expansion", "dissipation", "activation_rate", "transmittivity", "contact_response"]

class Genome:
    def __init__(self, rule_count, material_count, input_count):
        self.rule_count = rule_count
        self.material_count = material_count
        self.input_count = input_count
        self.score = 0.0

    def cppn(self, inputs):
        values = []
        for rule in self.rules:
            params = []
            for arg in rule[1:]:
                if arg[0] == "rule":
                    params.append(values[arg[1]])
                elif arg[0] == "constant":
                    params.append(arg[1])
                elif arg[0] == "input":
                    params.append(inputs[arg[1]])
            if rule[0] == "sine":
                v = math.sin(params[0])
                values.append(v/2 + 0.5)
            elif rule[0] == "cosine":
                v = math.cos(2*math.pi*params[0])
                values.append(v/2 + 0.5)
            elif rule[0] == "tanh":
                v = math.tanh(4*params[0]-2)
                values.append(v/2 + 0.5)
            elif rule[0] == "gaussian":
                v = gauss(6*params[0] - 3)
                values.append(v)
            elif rule[0] == "mean":
                v = (params[0] + params[1])/2
                values.append(v)
            elif rule[0] == "product":
                v = params[0]*params[1]
                values.append(v)
            elif rule[0] == "ramp":
                v = 2*params[0] % 1
                values.append(v)
            elif rule[0] == "step":
                v = step(params[0])
                values.append(v)
            elif rule[0] == "spike":
                v = spike(params[0])
                values.append(v)
            elif rule[0] == "inverse":
                v = 1.0 - params[0]
                values.append(v)

        outputs = values[-(self.material_count+1):]
        material_index = max(range(self.material_count), 
                key=lambda x:outputs[x+1])
        return outputs[0], self.materials[material_index]

    def randomize(self):
        self.rules = [self.random_rule(i) \
                for i in xrange(self.rule_count)]
        self.materials = [self.random_material() \
                for _ in xrange(self.material_count)]

    def random_rule(self, index):
        rule = []
        func = random.choice(rules)
        rule.append(func[0])
        for j in xrange(func[1]):
            rule.append(self.random_parameter(index, 
                True if j>0 else False))

        return rule

    def random_parameter(self, index, allow_constant):
        if random.random() < 1.0*index/self.rule_count:
            return ["rule", random.randint(0, index-1)]
        elif allow_constant and random.random() < 0.5:
            return ["constant", random.random()*4-2]
        else:
            return ["input", random.randint(0, self.input_count-1)]

    def random_material(self):
        material = []
        for p in properties:
            material.append([p, random.random()])
        return material

    def mutate(self, r):
        for i in xrange(self.rule_count):
            rand = random.random()
            if rand < r/2:
                self.rules[i] = self.random_rule(i)
            elif rand < r:
                rule = self.rules[i]
                j = random.randint(1, len(rule)-1)
                rule[j] = self.random_parameter(i, True if j>0 else False)

        for i in xrange(self.material_count):
            rand = random.random()
            if rand < r/2:
                self.materials[i] = self.random_material()
            else:
                j = random.randint(0, len(properties)-1)
                self.materials[i][j][1] = random.random()

    def crossover(self, other):
        i = random.randint(0, self.rule_count)
        j = random.randint(0, self.rule_count)
        if j < i:
            i, j = j, i

        temp = self.rules[i:j]
        self.rules = self.rules[:i]+other.rules[i:j]+self.rules[j:]
        other.rules = other.rules[:i]+temp+other.rules[j:]

        i = random.randint(0, self.material_count)
        j = random.randint(0, self.material_count)
        if j < i:
            i, j = j, i
        temp = self.materials[i:j]
        self.materials = self.materials[:i]+other.materials[i:j]\
                +self.materials[j:]
        other.materials = other.materials[:i]+temp+other.materials[j:]

    def clone(self):
        g = Genome(self.rule_count, self.material_count, self.input_count)

        g.rules = []
        for rule in self.rules:
            g.rules.append([p[:] for p in rule])

	g.materials = []
	for material in self.materials:
	    g.materials.append([p[:] for p in material])

        g.score = self.score

        return g

    def __str__(self):
        s = "rules: \n"
        for i in xrange(self.rule_count):
            rule = self.rules[i]
            s += "%d: %s " % (i, rule[0])
            for o in rule[1:]:
                s += str(o) + " "
            s += "\n"
        s += "\n"

        s += "materials:\n"
        for i in xrange(self.material_count):
            m = self.materials[i]
            for p in m:
                s += "%.4f  " % p[1]
            s += "\n"
        s += "\n"

        return s

def gauss(x):
    return math.e**(-x**2/2)

def step(x):
    if x % 1 > 0.5:
        return 1.0
    else:
        return 0.0

def spike(x):
    y = 2*(x % 1)
    if y > 1:
        y = 2 - y
    return y
