import numpy as np

class Organism:
    def __init__(self, x, y, speed, vision, size, food, hunger, max_hunger, efficiency, repr, pred, move_cost):
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
        return


    def scan(self, landscape, looking_for):

        landscape_size = len(landscape)
        distances, locations = [], []
        for dx in range(-self.vision, self.vision + 1):
            x = self.x + dx
            if x >= landscape_size or x < 0:
                continue

            for dy in range(-self.vision, self.vision + 1):
                y = self.y + dy
                if y >= landscape_size or y < 0:
                    continue

                ds = (dx**2 + dy**2)
                distances.append(ds)
                locations.append((x, y))

        indices = np.argsort(distances)
        distances = np.asarray(distances)[indices]
        locations = np.asarray(locations)[indices]

        found = []
        for i, (x, y) in enumerate(locations):
            for e in landscape[x, y]:
                if isinstance(e, looking_for) and e is not self and e.alive:
                    found.append((e, distances[i]))

        return found



    def behavior(self, landscape):
        if not self.alive:
            return
        
        landscape_size = len(landscape)

        # Check if predators are within vision range
        predators = self.scan(landscape, self.pred) if self.pred else []

        # Conditions 
        mate = self.hunger > self.repr * self.max_hunger
        food = self.hunger < 0.5 * self.max_hunger

        choices, probabilities = [], []
        if mate: 
            choices.append("mate"), probabilities.append(1.1)
        if food: 
            choices.append("food"), probabilities.append(0.9)
        if predators:
            choices.append("pred"), probabilities.append(5)

        choices.append("motionless"), probabilities.append(0.05)
        choices.append("random"), probabilities.append(0.1)
        choice = np.random.choice(choices, p = np.asarray(probabilities) / sum(probabilities))

        # Seek out mates
        if choice == "mate":
            mates = self.scan(landscape, type(self))   
            for e, ds in mates:
                    landscape[self.x, self.y].discard(self)
                    self.x = e.x
                    self.y = e.y
                    landscape[self.x, self.y].add(self)
                    return

        # Seek out food                    
        elif choice == "food":
            foods = self.scan(landscape, self.food)   
            for e, ds in foods:
                if (self.speed**2 >= ds):
                    self.hunger -= self.move_cost * 0.5 * self.size * ds
                    landscape[self.x, self.y].discard(self)
                    self.x = e.x
                    self.y = e.y
                    landscape[self.x, self.y].add(self)
                    return

        elif choice == "pred":
            return

        elif choice == "motionless":
            return

        elif choice == "random":
            return


    def is_dead(self, landscape):
        if self.hunger <= 0:
            landscape[self.x, self.y].discard(self)
            self.alive = False
            return True
        return False

#------------------------------------------------------------------------------#

class Plant(Organism):
    def __init__(self, name, x, y):
        super().__init__(
            x = x,
            y = y,
            speed=0,
            vision=0,
            size=np.random.randint(1, 6), 
            food=(), 
            hunger=100, 
            max_hunger=100,
            efficiency = 0,
            repr = 0,
            pred = None,
            move_cost = 0
        )
        self.name = name

class Rabbit(Organism):
    def __init__(self, name, x, y):   
        super().__init__(
            x = x,
            y = y,
            speed=np.random.randint(5, 11),
            vision=5,
            size=np.random.randint(1,8), 
            food=Plant, 
            hunger=np.random.randint(0.5*100, 101), 
            max_hunger=100,
            efficiency = 5,
            repr = 0.7,
            pred = Fox,
            move_cost = 0.02
        )
        self.name = name

class Fox(Organism):
    def __init__(self, name, x, y):   
        super().__init__(
            x = x,
            y = y,
            speed=np.random.randint(4, 8),
            vision=5,
            size=np.random.randint(5,12), 
            food=Rabbit, 
            hunger=np.random.randint(0.5*200, 200), 
            max_hunger=200,
            efficiency = 15,
            repr = 0.3,
            pred = None,
            move_cost = 0.02
        )
        self.name = name