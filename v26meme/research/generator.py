from __future__ import annotations
import random, hashlib
from typing import List, Dict, Any
from v26meme.core.dsl import Gene, StrategyCard
from v26meme.research.genes import GENE_POOL

class GeneticGenerator:
    def __init__(self, cfg: Dict[str, Any]):
        self.cfg = cfg['discovery']
        self.gene_pool = GENE_POOL
        self.population: List[StrategyCard] = []

    def _create_random_gene(self, category: str) -> Gene:
        gene_name = random.choice([k for k, v in self.gene_pool.items() if v['category'] == category])
        gene_info = self.gene_pool[gene_name]
        params = {p: random.choice(vals) for p, vals in gene_info['params'].items()}
        return Gene(name=gene_name, params=params, category=category)

    def _create_random_card(self) -> StrategyCard:
        genes = [self._create_random_gene('entry'), self._create_random_gene('exit_tp'), self._create_random_gene('exit_sl')]
        if random.random() > 0.5: genes.append(self._create_random_gene('filter'))
        gene_str = "".join(sorted([f"{g.name}{g.params}" for g in genes]))
        card_id = hashlib.sha256(gene_str.encode()).hexdigest()[:12]
        theme = self.gene_pool[genes[0].name]['theme']
        name = f"{theme}_{card_id}"
        return StrategyCard(id=card_id, name=name, theme=theme, genes=genes)

    def _crossover(self, p1: StrategyCard, p2: StrategyCard) -> StrategyCard:
        child_genes = [random.choice([next(g for g in p.genes if g.category==cat), next(g for g in p2.genes if g.category==cat)]) for cat in ['entry', 'exit_tp', 'exit_sl']]
        return StrategyCard(id=hashlib.sha256("".join(sorted([f"{g.name}{g.params}" for g in child_genes])).encode()).hexdigest()[:12], name=f"crossover_{p1.id[:4]}_{p2.id[:4]}", theme=self.gene_pool[child_genes[0].name]['theme'], genes=child_genes)

    def _mutate(self, card: StrategyCard) -> StrategyCard:
        mutated_genes = list(card.genes)
        idx = random.randrange(len(mutated_genes))
        mutated_genes[idx] = self._create_random_gene(mutated_genes[idx].category)
        return StrategyCard(id=hashlib.sha256("".join(sorted([f"{g.name}{g.params}" for g in mutated_genes])).encode()).hexdigest()[:12], name=f"mutate_{card.id[:6]}", theme=self.gene_pool[mutated_genes[0].name]['theme'], genes=mutated_genes)

    def initialize_population(self):
        self.population = [self._create_random_card() for _ in range(self.cfg['population_size'])]

    def run_evolution_cycle(self, fitness_scores: Dict[str, float]) -> List[StrategyCard]:
        if not self.population: self.initialize_population()
        new_pop = []
        sorted_pop = sorted(self.population, key=lambda c: fitness_scores.get(c.id, 0), reverse=True)
        elite_size = int(len(sorted_pop) * 0.1)
        new_pop.extend(sorted_pop[:elite_size])
        while len(new_pop) < self.cfg['population_size']:
            p1, p2 = random.choices(sorted_pop[:len(sorted_pop)//2], k=2)
            child = self._crossover(p1, p2) if random.random() < self.cfg['crossover_rate'] else p1
            if random.random() < self.cfg['mutation_rate']: child = self._mutate(child)
            new_pop.append(child)
        self.population = new_pop
        return self.population
