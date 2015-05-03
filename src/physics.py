import math

FRICTION_COEFFICIENT = 0.5
DAMPING_COEFFICIENT = 3.0
#g = 9.81
g = 20.0
EAST, NORTH, WEST, SOUTH = 0, 1, 2, 3

class Body(object):
    def __init__(self, mass, position):
        self.mass = mass
        self.position = position
        self.velocity = [0, 0]
        self.force = [0, 0]

    def step(self, delta_t):
        self.velocity[0] += self.force[0]*delta_t/self.mass
        self.velocity[1] += self.force[1]*delta_t/self.mass

        self.position[0] += self.velocity[0]*delta_t
        self.position[1] += self.velocity[1]*delta_t

        if self.position[1] < 0:
            self.position[0] -= self.velocity[0]*delta_t
            self.position[1] -= self.velocity[1]*delta_t

            self.velocity[0] -= self.velocity[0]*delta_t
            self.velocity[1] -= self.velocity[1]*delta_t

            counter_force = -(self.mass/delta_t) \
                    * (self.position[1]/delta_t + self.velocity[1]) \
                    - self.force[1]
            friction = counter_force*FRICTION_COEFFICIENT

            if self.velocity[0] < 0:
                self.force[0] += friction
                sign = -1
            else:
                self.force[0] -= friction
                sign = 1
            self.force[1] += counter_force

            before = self.velocity[0]
            self.velocity[0] += self.force[0]*delta_t/self.mass
            if self.velocity[0] < 0 and before > 0:
                self.velocity[0] = 0.0
            elif self.velocity[0] > 0 and before < 0:
                self.velocity[0] = 0.0
            self.velocity[1] += self.force[1]*delta_t/self.mass

            self.position[0] += self.velocity[0]*delta_t
            self.position[1] += self.velocity[1]*delta_t

        self.velocity[0] *= (1-delta_t*DAMPING_COEFFICIENT)
        self.velocity[1] *= (1-delta_t*DAMPING_COEFFICIENT)

        self.force = [0, 0]

    def push(self, f):
        self.force[0] += f[0]
        self.force[1] += f[1]

    def get_color(self):
        return [255, 255, 255]

class Cell(Body):
    def __init__(self, mass, position, axial_stiffness, bending_stiffness,
            expansion, dissipation, activation_rate, transmittivity, 
            contact_response):
        super(Cell, self).__init__(mass, position)

        self.axial_stiffness = axial_stiffness
        self.bending_stiffness = bending_stiffness
        self.expansion = expansion
        self.dissipation = dissipation
        self.activation_rate = activation_rate
        self.transmittivity = transmittivity
        self.contact_response = contact_response

        self.voltage = 0.0
        self.phase = 0
        self.phase_time = 0.0
        self.connections = [None, None, None, None]

    def connect(self, other, direction):
        self.connections[direction] = other

    def step(self, delta_t):
        if self.position[0] < 0.001 and self.contact_response \
                and self.phase == 0:
            self.voltage = 0.21

        if self.phase == 0 and self.voltage > 0.2:
            self.phase = 1
        elif self.phase == 1 and self.voltage > 1:
            self.phase = 2
        elif self.phase == 2 and self.voltage < -0.5:
            self.phase = 0

        if self.phase == 0:
            self.voltage *= (1-self.dissipation*delta_t)
        elif self.phase == 1:
            self.voltage += self.activation_rate*delta_t
        elif self.phase == 2:
            self.voltage -= self.activation_rate\
                *(self.voltage/2+0.5)*delta_t

        super(Cell, self).step(delta_t)

    def interact(self, delta_t):
        if self.phase == 1:
            for cell in self.connections:
                if cell and cell.phase == 0:
                    cell.charge(self.voltage*self.transmittivity*delta_t)

        # relative positions of connected cells
        delta_positions = [None, None, None, None]
        angles = [None, None, None, None]
        distances = [None, None, None, None]
        for i in xrange(4):
            cell = self.connections[i]
            if cell:
                delta_x = cell.position[0] - self.position[0]
                delta_y = cell.position[1] - self.position[1]
                angle = math.atan2(delta_y, delta_x)
                distance = (delta_x**2+delta_y**2)**0.5

                delta_positions[i] = [delta_x, delta_y]
                angles[i] = angle
                distances[i] = distance

        # radial forces to self
        for i in xrange(4):
            cell = self.connections[i]
            if cell:
                delta_x = delta_positions[i][0]
                delta_y = delta_positions[i][1]
                distance = distances[i]
                target = 2.0 + (self.expansion*self.voltage \
                        + cell.expansion*cell.voltage)/2

                force = (self.axial_stiffness+cell.axial_stiffness)\
                        *(distance-target)/2
                force_x = force*delta_x/distance
                force_y = force*delta_y/distance
                self.push([force_x, force_y])

        # torque on others
        for i in xrange(4):
            cell = self.connections[i]
            if cell:
                angle_correction = 0
                for j in xrange(4):
                    if i != j and self.connections[j]:
                        other = self.connections[j]
                        angle_correction += ((angles[j]-angles[i]) \
                                % (2*math.pi))
                        angle_correction -= (math.pi*((j-i) % 4)/2)
                force = self.bending_stiffness*angle_correction\
                        /distances[i]
                force_x = -force*delta_positions[i][1]/distances[i]
                force_y = force*delta_positions[i][0]/distances[i]
                self.connections[i].push([force_x, force_y])
                self.push([-force_x, -force_y])

    def charge(self, c):
        self.voltage += c

    def get_color(self):
        if self.voltage < -1:
            r = 255
            g = 0
            b = 0
        elif self.voltage < -0.667:
            r = 255
            g = 756*self.voltage + 756
            b = 0
        elif self.voltage < -0.333:
            r = -756*self.voltage - 255
            g = 255
            b = 0
        elif self.voltage < 0:
            r = 0
            g = 255
            b = 756*self.voltage + 255
        elif self.voltage < 0.333:
            r = 0
            g = -756*self.voltage + 255
            b = 255
        elif self.voltage < 0.667:
            r = 756*self.voltage - 255
            g = 0
            b = 255
        elif self.voltage < 1:
            r = 255
            g = 0
            b = -756*self.voltage + 756
        else:
            r = 255
            g = 0
            b = 0

        color = [int(r), int(g), int(b)]
        for i in xrange(3):
            if color[i] < 0:
                color[i] = 0
            elif color[i] > 255:
                color[i] = 255

        return color

class World:
    def __init__(self, delta_t):
        self.delta_t = delta_t
        self.bodies = []
        self.agents = []

    def add_body(self, body):
        self.bodies.append(body)

    def add_agent(self, agent):
        self.agents.append(agent)
        for b in agent.cells:
            self.add_body(b)

    def step(self):
        for b in self.bodies:
            b.push([0, -g*b.mass])
        for a in self.agents:
            a.step(self.delta_t)
        for b in self.bodies:
            b.step(self.delta_t)
