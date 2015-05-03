from physics import Cell, g

EAST, NORTH, WEST, SOUTH = 0, 1, 2, 3

def transform_properties(before):
    after = []
    for p in before:
        if p[0] == "axial_stiffness":
            after.append([p[0], p[1]*1000])
        elif p[0] == "bending_stiffness":
            after.append([p[0], p[1]*500])
        elif p[0] == "expansion":
            after.append([p[0], p[1]*1.8-0.9])
        elif p[0] == "dissipation":
            after.append([p[0], p[1]*5])
        elif p[0] == "activation_rate":
            after.append([p[0], p[1]*5])
        elif p[0] == "transmittivity":
            after.append([p[0], p[1]*5])
        elif p[0] == "contact_response":
            after.append([p[0], True if p[1]>0.5 else False])

    return after

class Agent:
    def __init__(self, genome, grid_size, max_cell_count, 
            pacemaker_period):
        self.grid_size = grid_size
        self.grid = [[False]*grid_size for _ in xrange(grid_size)]
        i_center = grid_size/2
        j_center = grid_size/2

        self.cells = []
        self.frontier = []
        self.cell_count = 0

        self.pacemaker = Cell(1.0, [0.0, 0.0], 10, 15, 
                0.0, 0.5, 0.5, 1.0, 0.0)
        self.pacemaker_period = pacemaker_period
        self.pacemaker_timer = 0.0
        self.add_cell(self.pacemaker, i_center, j_center)

        while len(self.frontier) > 0 and self.cell_count < max_cell_count:
            i, j = self.frontier.pop(0)
            x = 1.0*(j - j_center)
            y = 1.0*(i_center - i)
            r = (x**2 + y**2)**0.5
            adjacent_count = 0
            for i_p, j_p in self.adjacent_indices(i, j):
                adjacent = self.grid[i_p][j_p]
                if isinstance(adjacent, Cell):
                    adjacent_count += 1

            x_in = x/grid_size + 0.5
            y_in = y/grid_size + 0.5
            r_in = 1.414*(x**2 + y**2)**0.5/grid_size
            adj_in = (adjacent_count - 1)/3.0

            growth, properties = genome.cppn([x_in, y_in, r_in, adj_in])
            if growth > (1.0 - 1.0*self.cell_count/max_cell_count)**2:
                self.grid[i][j] = False
                continue
            properties = transform_properties(properties)
            for p in properties:
                if p[0] == "axial_stiffness":
                    axial_stiffness = p[1]
                elif p[0] == "bending_stiffness":
                    bending_stiffness = p[1]
                elif p[0] == "expansion":
                    expansion = p[1]
                elif p[0] == "dissipation":
                    dissipation = p[1]
                elif p[0] == "activation_rate":
                    activation_rate = p[1]
                elif p[0] == "transmittivity":
                    transmittivity = p[1]
                elif p[0] == "contact_response":
                    contact_response = p[1]

            cell = Cell(1.0, [x, y], axial_stiffness, 
                    bending_stiffness, expansion, dissipation, 
                    activation_rate, transmittivity, contact_response)
            self.add_cell(cell, i, j)

    def add_cell(self, cell, i, j):
        self.cells.append(cell)
        self.cell_count += 1
        self.grid[i][j] = cell

        for i_p, j_p in self.adjacent_indices(i, j):
            adj = self.grid[i_p][j_p]
            if adj == False:
                self.grid[i_p][j_p] = True
                self.frontier.append([i_p, j_p])
            elif isinstance(adj, Cell):
                if j_p > j:
                    direction = EAST
                    opposite = WEST
                elif i_p < i:
                    direction = NORTH
                    opposite = SOUTH
                elif j_p < j:
                    direction = WEST
                    opposite = EAST
                elif i_p > i:
                    direction = SOUTH
                    opposite = NORTH
                cell.connect(adj, direction)
                adj.connect(cell, opposite)

    def adjacent_indices(self, i, j):
        directions = [[0, 1], [-1, 0], [0, -1], [1, 0]]
        adjacent = []
        for direction in directions:
            i_p = i + direction[0]
            j_p = j + direction[1]
            if i_p < 0 or i_p >= self.grid_size:
                continue
            elif j_p < 0 or j_p >= self.grid_size:
                continue
            else:
                adjacent.append([i_p, j_p])

        return adjacent

    def step(self, delta_t):
        if self.pacemaker_timer >= self.pacemaker_period:
            self.pacemaker.voltage = 0.21
            self.pacemaker_timer %= self.pacemaker_period
        for c in self.cells:
            c.interact(delta_t)
        self.pacemaker_timer += delta_t

    def translate(self, delta_position):
        for c in self.cells:
            c.position[0] += delta_position[0]
            c.position[1] += delta_position[1]

    def center_of_mass(self):
        mass_sum = 0.0
        x_sum = 0.0
        y_sum = 0.0
        for cell in self.cells:
            mass_sum += cell.mass
            x_sum += cell.mass*cell.position[0]
            y_sum += cell.mass*cell.position[1]

        return [x_sum/mass_sum, y_sum/mass_sum]
