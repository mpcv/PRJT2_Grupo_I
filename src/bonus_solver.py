import math
import time
import random
from lineup import ScheduleBuilder
from metaheuristic import SimulatedAnnealing

class BonusScheduleBuilder(ScheduleBuilder):
    def evaluate(self, solution):
        #1. Avaliar o Consumo Global de Recursos N
        total_n = [0] * self.instance.num_nonrenewable
        for job, mode in solution.modes.items():
            if job not in self.instance.modes_data: continue
            req = self.instance.modes_data[job][mode]["N"]
            for i in range(self.instance.num_nonrenewable):
                total_n[i] += req[i]

        #Custo de recursos N excedentes (AN)
        an_cost = 0
        for i in range(self.instance.num_nonrenewable):
            deficit = max(0, total_n[i] - self.instance.res_capacities["N"][i])
            an_cost += deficit

        #2. Agendamento Rápido (Sem bloqueio por limites de recursos R)
        horizon_limit = max(self.instance.horizon, sum(self.instance.modes_data[j][solution.modes[j]]["duration"] for j in self.instance.modes_data))
        time_res_profile = [[0] * self.instance.num_renewable for _ in range(horizon_limit + 100)]
        completion_times = {i: 0 for i in range(1, self.instance.num_jobs + 1)}
        solution.start_times = {}

        for job in solution.sequence:
            if job not in self.instance.modes_data:
                completion_times[job] = 0 if job == 1 else max([completion_times[p] for p in self.predecessors[job]] + [0])
                continue

            mode = solution.modes[job]
            duration = self.instance.modes_data[job][mode]["duration"]
            req_r = self.instance.modes_data[job][mode]["R"]

            # Tarefa arranca no Earliest Start Time ditado pelas precedências
            start_time = max([completion_times[p] for p in self.predecessors[job]] + [0])
            
            for t in range(start_time, start_time + duration):
                for r in range(self.instance.num_renewable):
                    time_res_profile[t][r] += req_r[r]

            solution.start_times[job] = start_time
            completion_times[job] = start_time + duration

        solution.makespan = completion_times[self.instance.num_jobs]

        # 3. Calcular Custo de Pico de Recursos R (AR)
        ar_cost = 0
        for r in range(self.instance.num_renewable):
            pico_maximo = max([time_res_profile[t][r] for t in range(solution.makespan + 1)] + [0])
            deficit = max(0, pico_maximo - self.instance.res_capacities["R"][r])
            ar_cost += deficit
        
        # Nova Métrica Z = Cmax + AN + AR
        solution.is_feasible = True
        solution.bonus_objective = solution.makespan + an_cost + ar_cost
        
        return True
    

class BonusSimulatedAnnealing(SimulatedAnnealing):

    def _clone_solution(self, solution):
        #Cria o clone usando a lógica original
        new_sol = super()._clone_solution(solution)
        #Garante que a nova métrica bónus passa para o clone em memória
        if hasattr(solution, 'bonus_objective'):
            new_sol.bonus_objective = solution.bonus_objective
        return new_sol

    # Qualquer modo é válido pois podemos "comprar" recursos, sem barreiras de viabilidade
    def _modo_e_viavel_em_recursos(self, job, modo):
        return True 

    # Sobreescreve o motor de Simulated Annealing para usar 'bonus_objective' no arrefecimento
    def run(self, initial_solution, time_limit=None, max_iterations=None, target_makespan=None):
        start_time = time.time()
        
        current = self._clone_solution(initial_solution)
        self.builder.evaluate(current)
        
        best = self._clone_solution(current)
        history = [best.bonus_objective]
        total_iterations = 0
        restarts = 0
        max_restarts_no_time_limit = 5

        while True:
            if restarts == 0:
                temperature = self.initial_temp
            else:
                current = self._clone_solution(best)
                temperature = self.initial_temp * 1.2

            while temperature > self.min_temp:
                for _ in range(self.iterations_per_temp):
                    total_iterations += 1

                    if time_limit is not None and (time.time() - start_time) >= time_limit:
                        return best, history
                    if max_iterations is not None and total_iterations >= max_iterations:
                        return best, history
                    
                    neighbor = self._generate_neighbor(current)
                    if neighbor is None:
                        continue
                    
                    self.builder.evaluate(neighbor)
                
                    # A avaliação térmica para aceitar ou rejeitar é feita pelo novo custo total (Z)
                    delta = neighbor.bonus_objective - current.bonus_objective

                    if delta < 0:
                        current = neighbor
                        if current.bonus_objective < best.bonus_objective:
                            best = self._clone_solution(current)
                    else:
                        probability = math.exp(-delta / temperature) if temperature > 0 else 0
                        if random.random() < probability:
                            current = neighbor
                    
                    history.append(best.bonus_objective)

                temperature *= self.cooling_rate
            
            restarts += 1
            if time_limit is None and restarts >= max_restarts_no_time_limit:
                break
        
        return best, history