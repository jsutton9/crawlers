import time
import math
import random
import sys
import os
import multiprocessing
import re
import pickle

from src.genetics import Genome
from src.agents import Agent
from src.physics import World
from src.graphics import Display

display_width = 1200
display_height = 700
run_time = 1*60*60
scoring_process_count = 5

population_size = 20
mutation_rate = 0.02
crossover_rate = 0.02
delta_t = 0.01
evaluation_time = 20

rule_count = 200
material_count = 5
input_count = 4

max_cell_count = 30
pacemaker_period = 1.0

input_file_name = None
output_file_name = None

def score_genome(genome):
    agent = Agent(genome, grid_size, 
            max_cell_count, pacemaker_period)
    agent.translate([0, grid_size/2+1])
    world = World(delta_t)
    world.add_agent(agent)

    x_start = agent.center_of_mass()[0]

    sim_timer = 0.0
    while sim_timer < evaluation_time:
        world.step()
        sim_timer += delta_t

    delta_x = agent.center_of_mass()[0] - x_start
    genome.score = abs(delta_x)
    genome.score *= 0.5 + 0.5*agent.cell_count/max_cell_count
    return genome.score

def score_group(genomes, scoring_queue):
    for j, genome in genomes:
        s = score_genome(genome)
        scoring_queue.put([j, s])

def multiprocess_score(genomes):
    scoring_queue = multiprocessing.Queue()
    scoring_processes = []
    for i in xrange(scoring_process_count):
        group = []
        for j in xrange(i*agents_per_process, (i+1)*agents_per_process):
            if j < len(genomes):
                group.append([j, genomes[j]])
        process = multiprocessing.Process(target=score_group,
                args=(group,scoring_queue))
        process.start()
        scoring_processes.append(process)
    for process in scoring_processes:
        process.join()
    while not scoring_queue.empty():
        j, score = scoring_queue.get()
        genomes[j].score = score

def demonstrate(genome, queue):
    world = World(delta_t)
    agent = Agent(genome, grid_size, max_cell_count, pacemaker_period)
    agent.translate([0, grid_size/2+1])
    world.add_agent(agent)
    display = Display(world, display_width, display_height)

    step_count = int(math.ceil(0.05/delta_t))
    display_time = time.time()
    while True:
        if not queue.empty():
            while not queue.empty():
                queue.get()
            display.kill()
            return

        for _ in xrange(step_count):
            world.step()

        display.refresh()
        current_time = time.time()
        if current_time - display_time < 0.05:
            time.sleep(0.05 - current_time + display_time)
        display_time = current_time

def read_parameters(f):
    for line in f:
        match = re.match("\\s*([a-zA-Z_]+)\\s*=\\s*([^\\s]+)$", line)
        if match != None:
            name = match.group(1)
            value = match.group(2)
            if name == "display_width":
                global display_width
                display_width = int(value)
            elif name == "display_height":
                global display_height
                display_height = int(value)
            elif name == "run_time":
                global run_time
                run_time = int(value)
            elif name == "scoring_process_count":
                global scoring_process_count
                scoring_process_count = int(value)
            elif name == "population_size":
                global population_size
                population_size = int(value)
            elif name == "mutation_rate":
                global mutation_rate
                mutation_rate = float(value)
            elif name == "crossover_rate":
                global crossover_rate
                crossover_rate = float(value)
            elif name == "delta_t":
                global delta_t
                delta_t = float(value)
            elif name == "evaluation_time":
                global evaluation_time
                evaluation_time = int(value)
            elif name == "rule_count":
                global rule_count
                rule_count = int(value)
            elif name == "material_count":
                global material_count
                material_count = int(value)
            elif name == "max_cell_count":
                global max_cell_count
                max_cell_count = int(value)
            elif name == "pacemaker_period":
                global pacemaker_period
                pacemaker_period = float(value)
            elif name == "input_file":
                global input_file_name
                input_file_name = value
            elif name == "output_file":
                global output_file_name
                output_file_name = value

if len(sys.argv) == 2:
    if os.path.isfile(sys.argv[1]):
        read_parameters(open(sys.argv[1], 'r'))
    else:
        print "\"%s\" not found" % sys.argv[1]
        sys.exit()
elif len(sys.argv) > 2:
    print "Usage: python evolve.py [CONFIG_FILE]"
    sys.exit()

agents_per_process = \
        int(math.ceil(1.0*population_size/scoring_process_count))
grid_size = max_cell_count/2

if input_file_name != None and os.path.isfile(input_file_name):
    input_file = open(input_file_name, 'r')
    genomes = pickle.load(input_file)
    input_file.close()

    if len(genomes) > population_size:
        genomes = genomes[:population_size]
    elif len(genomes) < population_size:
        start_size = len(genomes)
        for i in xrange(len(genomes), population_size):
            genomes.append(genomes[i%start_size].clone())
            genomes[i].mutate(mutation_rate)
else:
    genomes = [Genome(rule_count, material_count, input_count) \
            for _ in xrange(population_size)]
    for genome in genomes:
        genome.randomize()
        a = Agent(genome, grid_size, max_cell_count, pacemaker_period)
        while a.cell_count <= 1:
            a = Agent(genome, grid_size, max_cell_count, pacemaker_period)
            genome.randomize()

multiprocess_score(genomes)
best_genome = None
demo_queue = multiprocessing.Queue()
demo_process = None

t0 = time.time()
generation_count = 0
while time.time() < t0+run_time:
    multiprocess_score(genomes)
    genomes.sort(key=lambda g:-g.score)

    print "generation: %d" % generation_count
    print "best: %f" % genomes[0].score
    print ""

    if best_genome == None:
        best_genome = genomes[0].clone()
    elif genomes[0].score > best_genome.score:
        best_genome = genomes[0].clone()

    if demo_process != None:
        demo_queue.put("stop")
        demo_process.join()

    demo_process = multiprocessing.Process(target=demonstrate, 
            args=(genomes[0], demo_queue))
    demo_process.start()

    for i in xrange(population_size/2):
        j = population_size/2 + i
        genomes[j] = genomes[i].clone()
        genomes[j].mutate(mutation_rate)
    for i in xrange(population_size/2, population_size-1):
        if random.random() < crossover_rate:
            genomes[i].crossover(genomes[i+1])

    generation_count += 1

    if output_file_name != None:
        swap_file = open("population.swp", 'w')
        pickle.dump(genomes, swap_file)
        os.rename("population.swp", output_file_name)
        swap_file.close()

if demo_process != None:
    demo_queue.put("stop")
    demo_process.join()
