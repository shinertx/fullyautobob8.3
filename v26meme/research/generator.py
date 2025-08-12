import random
import json
import hashlib
from typing import List

class GeneticGenerator:
    def __init__(self, features: List[str], population_size: int):
        self.features = features
        self.operators = ['>', '<']
        self.logical_ops = ['AND', 'OR']
        self.population_size = population_size
        self.population = []

    def _create_random_condition(self):
        return [random.choice(self.features), random.choice(self.operators), random.uniform(-2.0, 2.0)]

    def _create_random_formula(self, d=2):
        if d > 0:
            return [self._create_random_formula(d-1), random.choice(self.logical_ops), self._create_random_formula(d-1)]
        else:
            return self._create_random_condition()

    def initialize_population(self): 
        self.population = [self._create_random_formula() for _ in range(self.population_size)]

    def run_evolution_cycle(self, fitness_scores: dict):
        if not self.population:
            self.initialize_population()

        str_pop = {json.dumps(f): f for f in self.population}
        sorted_pop = sorted(
            str_pop.keys(), 
            key=lambda s: fitness_scores.get(hashlib.sha256(s.encode()).hexdigest(), 0), 
            reverse=True
        )
        
        # Elitism: Keep the top 10%
        elite_count = max(1, int(len(sorted_pop) * 0.1))
        new_pop_str = sorted_pop[:elite_count]

        # Crossover and mutation
        while len(new_pop_str) < self.population_size:
            # Select parents from the top 50% of the population
            parent1_str, parent2_str = random.choices(sorted_pop[:len(sorted_pop)//2], k=2)
            
            # Crossover: Randomly pick one parent's formula
            child_formula = json.loads(random.choice([parent1_str, parent2_str]))

            # Mutation: 20% chance to mutate a value in a condition
            if random.random() < 0.2:
                # Get all condition subtrees (leaf nodes)
                condition_nodes = [n for n in self._get_subtrees(child_formula) if not isinstance(n[0], list)]
                if condition_nodes:
                    node_to_mutate = random.choice(condition_nodes)
                    # Mutate the numeric value
                    node_to_mutate[2] = random.uniform(-2.0, 2.0)
            
            new_pop_str.append(json.dumps(child_formula))

        self.population = [json.loads(s) for s in new_pop_str]

    def _get_subtrees(self, formula):
        """Recursively get all subtrees from a formula."""
        nodes = []
        q = [formula]
        while q:
            node = q.pop(0)
            nodes.append(node)
            if isinstance(node[0], list):
                q.append(node[0])
            if len(node) > 1 and isinstance(node[2], list):
                q.append(node[2])
        return nodes