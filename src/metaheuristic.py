import math
import random
import time
from data_reader import Solution

class SimulatedAnnealing:
    def __init__(self, instance, builder, initial_temp=100.0, cooling_rate=0.97,
                 min_temp=1e-3, iterations_per_temp=20, seed=None):
        self.instance = instance
        self.builder = builder
        self.initial_temp = initial_temp
        self.cooling_rate = cooling_rate
        self.min_temp = min_temp
        self.iterations_per_temp = iterations_per_temp

        if seed is not None:
            random.seed(seed)

    def _clone_solution(self,solution):
        new_sol = Solution(self.instance)
        new_sol.sequence = list(solution.sequence)
        new_sol.modes = dict(solution.modes)
        new_sol.start_times = dict(solution.start_times)
        new_sol.makespan = solution.makespan
        new_sol.is_feasible = solution.is_feasible
        return new_sol

    def _neighbor_swap_sequence(self,solution):
        sequence = solution.sequence
        n = len(sequence)
        valid_swaps = []

        #Procura pares adjacentes que possam ser trocados em segurança
        for i in range(1, n-2):
            job_a = sequence[i]
            job_b = sequence[i+1]

            #Se a tarefa A não for predecessora da tarefa B, podemos trocá-las
            if job_a not in self.instance.predecessors.get(job_b, []):
                valid_swaps.append(i)
    
        if not valid_swaps:
            return None

        #Escolhe um par válido aleatoriamente e faz a troca
        swap_idx = random.choice(valid_swaps)

        new_sequence = list(sequence)
        new_sequence[swap_idx], new_sequence[swap_idx+1] = new_sequence[swap_idx+1], new_sequence[swap_idx]

        new_sol = self._clone_solution(solution)
        new_sol.sequence = new_sequence
        new_sol.start_times = {}

        return new_sol
    
    def _modo_e_viavel_em_recursos(self, job, modo):
        req_r = self.instance.modes_data[job][modo]['R']
        return all(req_r[r] <= self.instance.res_capacities['R'][r]
                    for r in range(self.instance.num_renewable))

    def _neighbor_change_mode(self,solution):
        candidatos = [job for job in self.instance.modes_data.keys()
                        if len(self.instance.modes_data[job]) > 1]
        
        if not candidatos:
            return None
        
        job = random.choice(candidatos)
        modo_atual = solution.modes[job]
        outros_modos = [m for m in self.instance.modes_data[job].keys()
                        if m != modo_atual and self._modo_e_viavel_em_recursos(job, m)]

        if not outros_modos:
            return None

        novo_modo = random.choice(outros_modos)
        new_sol = self._clone_solution(solution)
        new_sol.modes[job] = novo_modo
        new_sol.start_times = {}
        return new_sol
    
    def _neighbor_double_mode_changes (self,solution):
    #Troca o modo de duas tarefas em simultâneo para tentar contornar a falta de recursos N
        candidatos = [job for job in self.instance.modes_data.keys()
                        if len(self.instance.modes_data[job]) > 1]
        
        if len(candidatos) < 2:
            return None
        
        job1, job2 = random.sample(candidatos,2)

        modo_atual1 = solution.modes[job1]
        outros_modos1 = [m for m in self.instance.modes_data[job1].keys()
                        if m != modo_atual1 and self._modo_e_viavel_em_recursos(job1,m)]

        modo_atual2 = solution.modes[job2]
        outros_modos2 = [m for m in self.instance.modes_data[job2].keys()
                        if m != modo_atual2 and self._modo_e_viavel_em_recursos(job2,m)]

        if not outros_modos1 or not outros_modos2:
            return None