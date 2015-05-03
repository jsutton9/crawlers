import Tkinter

from physics import Body, Cell, World

class Display:
    def __init__(self, world, width, height):
        global canvas
        global image

        self.world = world
        self.width = width
        self.height = height

        self.scale = 10000.0
        self.left_edge = -width/(2*self.scale)
        self.right_edge = width/(2*self.scale)
        self.top_edge = height/(self.scale)

        self.root = Tkinter.Tk()
        canvas = Tkinter.Canvas(self.root, width=width, 
                height=height, bg="black")
        canvas.pack()

    def refresh(self):
        canvas.delete("all")
        bodies = self.world.bodies
        x_min = float("inf")
        x_max = -float("inf")
        y_max = 0
        for b in bodies:
            if b.position[0] < x_min:
                x_min = b.position[0]
            if b.position[0] > x_max:
                x_max = b.position[0]
            if b.position[1] > y_max:
                y_max = b.position[1]

        middle = (self.left_edge+self.right_edge)/2
        while x_min < self.left_edge and x_max > middle \
                or x_min < middle and x_max > self.right_edge \
                or y_max > self.top_edge:
            self.scale /= 2
            self.top_edge *= 2
            self.left_edge -= middle - self.left_edge
            self.right_edge += self.right_edge - middle
        while x_min < self.left_edge and x_max < middle:
            self.right_edge = middle
            middle = self.left_edge
            self.left_edge -= self.right_edge - middle
        while x_min > middle and x_max > self.right_edge:
            self.left_edge = middle
            middle = self.right_edge
            self.right_edge += middle - self.left_edge

        for b in bodies:
            x = b.position[0]
            y = b.position[1]
            x0 = self.scale*(x-self.left_edge) - 5
            y0 = self.height-self.scale*y - 5
            x1 = self.scale*(x-self.left_edge) + 5
            y1 = self.height-self.scale*y + 5
            color = "#%02x%02x%02x" % tuple(b.get_color())
            canvas.create_oval(x0, y0, x1, y1, fill=color)

        cells = []
        for a in self.world.agents:
            cells += a.cells
        for c0 in cells:
            x = c0.position[0]
            y = c0.position[1]
            x0 = self.scale*(x-self.left_edge)
            y0 = self.height-self.scale*y
            for c1 in c0.connections[:2]:
                if c1:
                    x = c1.position[0]
                    y = c1.position[1]
                    x1 = self.scale*(x-self.left_edge)
                    y1 = self.height-self.scale*y
                    canvas.create_line(x0, y0, x1, y1, width=2, 
                            fill="white")

        canvas.update()

    def kill(self):
        self.root.withdraw()
