import animals
import time
import numpy as np
import matplotlib.pyplot as plt

#------------------------------------------------------------------------------#

# Initial Game Settings #  
    # Total amount of starting organisms (excluding plants)
in_pop = 300
    # Amount of cycles to run the simulation for
set_cycles = 500
    # Landscape grid size (nxn array)
landscape_size = 100
    # The amount of plants than can spawn each cycle (min, max)
set_plants = (5, 30)
    # Maximum amount of possible plants
max_plants = 5000

#------------------------------------------------------------------------------#

# Landscape Generation #
landscape = np.zeros((landscape_size, landscape_size), dtype = object)
for r in range(landscape_size):
    for c in range(landscape_size):
        landscape[r,c] = set()

#------------------------------------------------------------------------------#

# Initialisation #

    # Defines a function that counts the animals for me. Used in the while loop.
def count_animals(landscape):
    density = np.zeros((landscape_size, landscape_size), dtype=int)
    plants = 0
    rabbits = 0
    foxes = 0
    for r in range(landscape_size):
        for c in range(landscape_size):
            for entity in landscape[r, c]:
                if isinstance(entity, animals.Plant):
                    plants += 1 
                else: 
                    density[r, c] += 1
                    if isinstance(entity, animals.Rabbit):
                        rabbits += 1 
                    if isinstance(entity, animals.Fox):
                        foxes += 1
    return density, plants, rabbits, foxes


    # Generate population of random animals
animal_classes = [
    animals.Rabbit,
    animals.Fox
    ]

for i in range(in_pop):
    row = np.random.randint(0, landscape_size)
    column = np.random.randint(0, landscape_size)

    animalclass = np.random.choice(animal_classes)
    animal = animalclass(x = row, y = column, name = 'Animal')

    landscape[row, column].add(animal)

    # Counters for info generation
total_cycles = 0
density_history = np.zeros((landscape_size, landscape_size))
plant_history = []
rabbit_history = []
fox_history = []


start = time.time()
print("\033[92mStarted simulation!\033[0m")
print("Elapsed Time: 0.00 seconds")
print("Cycles: 0")
print("Rabbits: 0")
print("Foxes: 0")
print("Plants: 0")

#------------------------------------------------------------------------------#

# Start of Simulation #

while total_cycles < set_cycles:

    # Initialize counting function
    density, plants, rabbits, foxes = count_animals(landscape)

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

    # End simulation if all populations are 0
    if density.sum() == 0:
        break   


    # Adding plants to random places in the landscape
    if plants < max_plants:
        plant_spawn_range = np.random.randint(*set_plants)
        for p in range(plant_spawn_range):

            row = np.random.randint(0, landscape_size)
            column = np.random.randint(0, landscape_size)

            plant = animals.Plant(x = row, y = column, name = 'plant')
            landscape[row, column].add(plant) 


    # Entity actions:
        # Move --> Eat --> Reproduce --> Die(?)
    actors = [e for row in landscape for cell in row for e in cell
              if not isinstance(e, animals.Plant)]
    np.random.shuffle(actors)

    for entity in actors:
        if entity.alive:
        # General actions
            entity.behavior(landscape)
            entity.eat(landscape[entity.x, entity.y])
            entity.is_dead(landscape)

    # Reproduction
    for row in landscape:
        for cell in row:
            entity_list = [e for e in cell if not isinstance(e, animals.Plant)]
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

                        baby = type(a)(x = a.x, y = a.y, name = 'animal',)
                        baby.hunger = ((a.hunger + b.hunger) * 0.5)
                        landscape[a.x, a.y].add(baby)

#------------------------------------------------------------------------------#
# Info Generation #

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

    # Heat Map #

ax2.imshow(
    (np.asarray(density_history)/total_cycles),
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