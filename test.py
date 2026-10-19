"""
Ecosystem simulation: rabbits, foxes and plants on a grid, with a live view.
Everything is in this one file, so just run it.
"""
import time
from functools import lru_cache

import numpy as np
import matplotlib.pyplot as plt

#------------------------------------------------------------------------------#
# Settings #
#------------------------------------------------------------------------------#

    # Total amount of starting animals (excluding plants)
in_pop = 300
    # Amount of cycles to run the simulation for
set_cycles = 500
    # Landscape grid size (nxn array)
landscape_size = 100
    # The amount of plants that can spawn each cycle (min, max)
set_plants = (5, 30)
    # Maximum amount of possible plants
max_plants = 5000
    # Hunger lost every cycle just for being alive, multiplied by the animal's
    # size. Without this, animals that stand still never starve. Set to 0 to disable.
upkeep = 0.1
    # Redraw the live view every N cycles (raise this if the drawing slows things down)
show_every = 1

#------------------------------------------------------------------------------#
# Organisms #
#------------------------------------------------------------------------------#

@lru_cache(maxsize=None)
def sorted_offsets(vision):
    """All (dx, dy, squared distance) within vision, nearest first.
    Built once per vision value instead of on every scan."""
    offsets = [(dx, dy, dx*dx + dy*dy)
               for dx in range(-vision, vision + 1)
               for dy in range(-vision, vision + 1)]
    offsets.sort(key=lambda o: o[2])
    return offsets


class Organism:
    def __init__(self, x, y, speed, vision, size, food, hunger, max_hunger,
                 efficiency, repr, pred, move_cost):
        self.x = x
        self.y = y
        self.speed = speed
        self.vision = vision
        self.size = size
        self.food = food
        self.hunger = hunger
        self.max_hunger = max_hunger
        self.efficiency = efficiency
        self.repr = repr
        self.pred = pred
        self.move_cost = move_cost
        self.alive = True

    def __repr__(self):
        return f"<{type(self).__name__}: {self.name}>"

    def eat(self, cell):
        for creature in cell.copy():
            if self.hunger >= self.max_hunger:
                return
            if creature is self:
                continue
            if isinstance(creature, self.food):
                self.hunger += self.efficiency * creature.size
                cell.discard(creature)
                creature.alive = False
        if self.hunger > self.max_hunger:
            self.hunger = self.max_hunger

    def scan(self, landscape, looking_for):
        """Every live `looking_for` in view as (entity, squared distance), nearest first."""
        n = len(landscape)
        found = []
        for dx, dy, ds in sorted_offsets(self.vision):
            x, y = self.x + dx, self.y + dy
            if 0 <= x < n and 0 <= y < n:
                for e in landscape[x, y]:
                    if isinstance(e, looking_for) and e is not self and e.alive:
                        found.append((e, ds))
        return found

    def _go(self, x, y, landscape):
        """Move to (x, y): swap cells and pay hunger for the distance actually moved."""
        dx, dy = x - self.x, y - self.y
        landscape[self.x, self.y].discard(self)
        self.x, self.y = x, y
        landscape[x, y].add(self)
        self.hunger -= self.move_cost * 0.5 * self.size * (dx**2 + dy**2)

    def behavior(self, landscape):
        if not self.alive:
            return

        n = len(landscape)

        # Check if predators are within vision range
        predators = self.scan(landscape, self.pred) if self.pred else []

        # Conditions
        mate = self.hunger > self.repr * self.max_hunger
        food = self.hunger < 0.5 * self.max_hunger

        choices, probabilities = [], []
        if mate:
            choices.append("mate")
            probabilities.append(1.1)
        if food:
            choices.append("food")
            probabilities.append(0.9)
        if predators:
            choices.append("pred")
            probabilities.append(5)
        choices.append("motionless")
        probabilities.append(0.05)
        choices.append("random")
        probabilities.append(0.1)
        choice = np.random.choice(choices, p=np.asarray(probabilities) / sum(probabilities))

        # Seek out mates
        if choice == "mate":
            for e, ds in self.scan(landscape, type(self)):
                if ds > self.speed**2:
                    break                      # nearest-first, so the rest are out of reach
                if e.hunger > e.repr * e.max_hunger:
                    self._go(e.x, e.y, landscape)
                    return

        # Seek out food
        elif choice == "food":
            for e, ds in self.scan(landscape, self.food):
                if ds > self.speed**2:
                    break
                self._go(e.x, e.y, landscape)
                return

        # Flee: push away from every predator in view, closer ones count more
        elif choice == "pred":
            fx = fy = 0.0
            for p, d2 in predators:
                if d2 == 0:                    # same cell: no direction
                    continue
                fx += (self.x - p.x) / d2
                fy += (self.y - p.y) / d2
            norm = (fx*fx + fy*fy) ** 0.5
            if norm == 0:                      # no clear direction: pick a random one
                angle = np.random.uniform(0, 2 * np.pi)
                fx, fy, norm = np.cos(angle), np.sin(angle), 1.0
            x = int(np.clip(round(self.x + fx / norm * self.speed), 0, n - 1))
            y = int(np.clip(round(self.y + fy / norm * self.speed), 0, n - 1))
            self._go(x, y, landscape)

        # Wander
        elif choice == "random":
            x = int(np.clip(self.x + np.random.randint(-self.speed, self.speed + 1), 0, n - 1))
            y = int(np.clip(self.y + np.random.randint(-self.speed, self.speed + 1), 0, n - 1))
            self._go(x, y, landscape)

        # "motionless": do nothing

    def is_dead(self, landscape):
        if self.hunger <= 0:
            landscape[self.x, self.y].discard(self)
            self.alive = False
            return True
        return False


class Plant(Organism):
    def __init__(self, name, x, y):
        super().__init__(
            x=x,
            y=y,
            speed=0,
            vision=0,
            size=np.random.randint(1, 6),
            food=(),
            hunger=100,
            max_hunger=100,
            efficiency=0,
            repr=0,
            pred=None,
            move_cost=0
        )
        self.name = name


class Rabbit(Organism):
    def __init__(self, name, x, y):
        super().__init__(
            x=x,
            y=y,
            speed=np.random.randint(5, 11),
            vision=5,
            size=np.random.randint(1, 8),
            food=Plant,
            hunger=np.random.randint(50, 101),
            max_hunger=100,
            efficiency=5,
            repr=0.7,
            pred=Fox,
            move_cost=0.02
        )
        self.name = name


class Fox(Organism):
    def __init__(self, name, x, y):
        super().__init__(
            x=x,
            y=y,
            speed=np.random.randint(4, 8),
            vision=5,
            size=np.random.randint(5, 12),
            food=Rabbit,
            hunger=np.random.randint(100, 200),
            max_hunger=200,
            efficiency=15,
            repr=0.3,
            pred=None,
            move_cost=0.02
        )
        self.name = name

#------------------------------------------------------------------------------#
# Landscape Generation #
#------------------------------------------------------------------------------#

landscape = np.zeros((landscape_size, landscape_size), dtype=object)
for r in range(landscape_size):
    for c in range(landscape_size):
        landscape[r, c] = set()

#------------------------------------------------------------------------------#
# Initialisation #
#------------------------------------------------------------------------------#

    # Counts everything for the graphs and collects positions for the live view.
    # x-axis of the view is the column, y-axis is the row.
def count_animals(landscape):
    density = np.zeros((landscape_size, landscape_size), dtype=int)
    plants = rabbits = foxes = 0
    plant_xy, rabbit_xy, fox_xy = [], [], []
    for r in range(landscape_size):
        for c in range(landscape_size):
            for entity in landscape[r, c]:
                if isinstance(entity, Plant):
                    plants += 1
                    plant_xy.append((c, r))
                else:
                    density[r, c] += 1
                    if isinstance(entity, Rabbit):
                        rabbits += 1
                        rabbit_xy.append((c, r))
                    elif isinstance(entity, Fox):
                        foxes += 1
                        fox_xy.append((c, r))
    return density, plants, rabbits, foxes, plant_xy, rabbit_xy, fox_xy


def as_points(xy):
    return np.array(xy, dtype=float).reshape(-1, 2)    # also handles an empty list


    # Generate population of random animals
animal_classes = [
    Rabbit,
    Fox
    ]

for i in range(in_pop):
    row = np.random.randint(0, landscape_size)
    column = np.random.randint(0, landscape_size)

    animalclass = np.random.choice(animal_classes)
    animal = animalclass(x=row, y=column, name='Animal')

    landscape[row, column].add(animal)

    # Counters for info generation
total_cycles = 0
density_history = np.zeros((landscape_size, landscape_size))
plant_history = []
rabbit_history = []
fox_history = []

    # Live view
plt.ion()
view_fig, view_ax = plt.subplots(figsize=(7, 7))
view_ax.set_xlim(-0.5, landscape_size - 0.5)
view_ax.set_ylim(landscape_size - 0.5, -0.5)      # inverted: row 0 at the top, like the heatmap
view_ax.set_aspect('equal')
view_ax.set_xticks([])
view_ax.set_yticks([])

    # plants are created first so they are drawn underneath the animals
plant_dots = view_ax.scatter([], [], s=3, c='green', alpha=0.4, label='Plants')
rabbit_dots = view_ax.scatter([], [], s=14, c='red', label='Rabbits')
fox_dots = view_ax.scatter([], [], s=26, c='orange', marker='^', label='Foxes')
view_ax.legend(loc='upper right', fontsize=8)

start = time.time()
print("\033[92mStarted simulation!\033[0m")
print("Elapsed Time: 0.00 seconds")
print("Cycles: 0")
print("Rabbits: 0")
print("Foxes: 0")
print("Plants: 0")

#------------------------------------------------------------------------------#
# Start of Simulation #
#------------------------------------------------------------------------------#

while total_cycles < set_cycles:

    # Initialize counting function
    density, plants, rabbits, foxes, plant_xy, rabbit_xy, fox_xy = count_animals(landscape)

    # Counters for graphs
    plant_history.append(plants)
    rabbit_history.append(rabbits)
    fox_history.append(foxes)
    density_history += density
    total_cycles += 1

    # Some debug stuff
    current_time = time.time() - start
    print(
        f"\033[5A"
        f"\033[KElapsed Time: {current_time:.2f} s\n"
        f"\033[KCycles: {total_cycles}\n"
        f"\033[KRabbits: {rabbits}\n"
        f"\033[KFoxes: {foxes}\n"
        f"\033[KPlants: {plants}\n",
        end="",
        flush=True)

    # Live view (drawn before the extinction check so the last frame is shown too)
    if total_cycles % show_every == 0:
        plant_dots.set_offsets(as_points(plant_xy))
        rabbit_dots.set_offsets(as_points(rabbit_xy))
        fox_dots.set_offsets(as_points(fox_xy))
        view_ax.set_title(f"Cycle {total_cycles}")
        plt.pause(0.001)

    # End simulation if all populations are 0
    if density.sum() == 0:
        break

    # Adding plants to random places in the landscape
    if plants < max_plants:
        plant_spawn_range = np.random.randint(*set_plants)
        for p in range(plant_spawn_range):

            row = np.random.randint(0, landscape_size)
            column = np.random.randint(0, landscape_size)

            plant = Plant(x=row, y=column, name='plant')
            landscape[row, column].add(plant)

    # Entity actions:
        # Upkeep --> Move --> Eat --> Die
    actors = [e for row in landscape for cell in row for e in cell
              if not isinstance(e, Plant)]
    np.random.shuffle(actors)

    for entity in actors:
        if entity.alive:
            entity.hunger -= upkeep * entity.size
            entity.behavior(landscape)
            entity.eat(landscape[entity.x, entity.y])
            entity.is_dead(landscape)

    # Reproduction
    for row in landscape:
        for cell in row:
            entity_list = [e for e in cell if not isinstance(e, Plant)]
            for i in range(len(entity_list)):
                for j in range(i + 1, len(entity_list)):
                    a, b = entity_list[i], entity_list[j]
                    if (
                        type(a) == type(b)
                        and a.hunger > a.repr * a.max_hunger
                        and b.hunger > b.repr * b.max_hunger
                        ):
                        a.hunger *= 0.5
                        b.hunger *= 0.5

                        baby = type(a)(x=a.x, y=a.y, name='animal')
                        baby.hunger = (a.hunger + b.hunger) * 0.5
                        landscape[a.x, a.y].add(baby)

#------------------------------------------------------------------------------#
# Info Generation #
#------------------------------------------------------------------------------#

    # Back to blocking mode so the final graphs stay open
plt.ioff()
plt.close(view_fig)      # remove this line to keep the live window open too

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

cycle_history = np.arange(0, len(rabbit_history))

    # Population graph
plant_plot = ax1.twinx()
plant_plot.plot(
    cycle_history,
    plant_history,
    color='green',
    linewidth=2,
    label='Plants'
)

ax1.plot(
    cycle_history,
    rabbit_history,
    color='red',
    linewidth=2,
    label='Rabbits'
)

ax1.plot(
    cycle_history,
    fox_history,
    color='orange',
    linewidth=2,
    label='Foxes'
)

ax1.set_title("Organism Populations Over Time")
ax1.set_xlabel("Cycle Number")
ax1.set_ylabel("Animal Count")
plant_plot.set_ylabel("Plant Count")

ax1.grid()

# Combine both legends
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = plant_plot.get_legend_handles_labels()

ax1.legend(
    lines1 + lines2,
    labels1 + labels2,
    loc='upper center',
    bbox_to_anchor=(0.5, -0.12),
    ncol=3
)

    # Heat Map
ax2.imshow(
    density_history / total_cycles,
    cmap='hot',
    origin='upper'
)

fig.colorbar(
    ax2.images[0],
    ax=ax2,
    label='Animals per cell'
)

ax2.set_title("Average Animal Density throughout Simulation")
ax2.set_xlabel("Column (y)")
ax2.set_ylabel("Row (x)")

plt.tight_layout()
plt.show()