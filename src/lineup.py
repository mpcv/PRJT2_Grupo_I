from data_reader import Solution
import random

class ScheduleBuilder:
    def __init__(self, instance):
        self.instance = instance
        #Aproveita os predecessores lidos no data_reader
        self.predecessors = self.instance.predecessors
    
    def gerar_solucao_inicial(self):
        solution = Solution(self.instance)
        modes = {}

        #1. Escolher os modos de cada tarefa
        for job in range(1, self.instance.num_jobs + 1):
            if job not in self.instance.modes_data:
                modes[job] = 1
                continue

            available_modes = self.instance.modes_data[job]
            valid_modes = {}

            for m, data in available_modes.items():
                is_valid = True
                for r in range(self.instance.num_renewable):
                    if data["R"][r] > self.instance.res_capacities["R"][r]:
                        is_valid = False
                        break
                if is_valid:
                    valid_modes[m] = data

            if not valid_modes:
                valid_modes = available_modes
            
            candidates = list(valid_modes.keys())

            #70% chance de poupar recursos N, 30% chance de escolher o modo mais rápido
            if random.random() < 0.70:
                best_mode = min(candidates, key=lambda m: (sum(valid_modes[m]["N"]), 0.3 * valid_modes[m]["duration"]))
            else:
                best_mode = min(candidates, key=lambda m: valid_modes[m]["duration"])

            modes[job] = best_mode

        #Ajuste de recursos N (tenta reparar a solução até 50)
        for _ in range(50):
            total_n = [0] * self.instance.num_nonrenewable
            for job, mode in modes.items():
                if job not in self.instance.modes_data:
                    continue
                consumo = self.instance.modes_data[job][mode]["N"]
                for i in range(self.instance.num_nonrenewable):
                    total_n[i] += consumo[i]
            
            excess_res = -1
            for i in range(self.instance.num_nonrenewable):
                if total_n[i] > self.instance.res_capacities["N"][i]:
                    excess_res = i
                    break

            #Se não há excesso, o ciclo para
            if excess_res == -1:
                break

            best_job = None
            best_mode = None
            max_reduction = 0

            #Procura um modo noutra tarefa que diminua o uso do recurso em excesso
            for job in modes:
                if job not in self.instance.modes_data:
                    continue

                current_mode = modes[job]
                current_cost = self.instance.modes_data[job][current_mode]["N"][excess_res]

                for new_mode, data in self.instance.modes_data[job].items():
                    if new_mode == current_mode:
                        continue

                    reduction = current_cost - data["N"][excess_res]
                    if reduction > max_reduction:
                        max_reduction = reduction
                        best_job = job
                        best_mode = new_mode

            if best_job is None:
                break

            modes[best_job] = best_mode
        
        solution.modes = modes

        #2. Gerar sequência topológica
        sequence = []
        eligible = [1]
        scheduled = set()

        while eligible:
            # Ordena a lista de elegíveis para priorizar tarefas críticas ou mais demoradas
            eligible.sort(
                key=lambda j: (len(self.instance.successors.get(j, [])),
                               self.instance.modes_data.get(j, {}).get(solution.modes[j], {}).get("duration", 0)),
                reverse=True
            )

            #Dá alguma aleatoriedade nas escolhas
            if random.random() < 0.80:
                job = eligible[0]
            else:
                job = random.choice(eligible[:min(3, len(eligible))])

            eligible.remove(job)
            sequence.append(job)
            scheduled.add(job)

            for succ in self.instance.successors.get(job, []):
                #Só adiciona o sucessor se todos os pais dele já estiverem agndados
                if all(p in scheduled for p in self.predecessors[succ]):
                    if succ not in eligible and succ not in scheduled:
                        eligible.append(succ)

        solution.sequence = sequence
        self.evaluate(solution)
        return solution
    
    def evaluate(self, solution):
        #Validação extra para os recursos N
        total_n = [0] * self.instance.num_nonrenewable
        for job, mode in solution.modes.items():
            if job not in self.instance.modes_data: continue
            req = self.instance.modes_data[job][mode]["N"]
            for i in range(self.instance.num_nonrenewable):
               total_n[i] += req[i]

        for i in range(self.instance.num_nonrenewable):
            if total_n[i] > self.instance.res_capacities["N"][i]:
                solution.is_feasible = False
                return False

        # SSGS - Construção da agenda baseada no tempo
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

            #Earliest Start Time
            est = max([completion_times[p] for p in self.predecessors[job]] + [0])
            start_time = est
            limite = len(time_res_profile) - duration

            #Procura janela com recursos disponíveis
            while start_time <= limite:
                if start_time + duration >= len(time_res_profile):
                    solution.is_feasible = False
                    return False
                
                is_valid = True
                for t in range(start_time, start_time + duration):
                    for r in range(self.instance.num_renewable):
                        if time_res_profile[t][r] + req_r[r] > self.instance.res_capacities["R"][r]:
                            is_valid = False
                            break
                    if not is_valid: break
                
                if is_valid: break
                start_time += 1

                if start_time > limite:
                    solution.is_feasible = False
                    return False
                
            #Regista consumos no perfil
            for t in range(start_time, start_time + duration):
                for r in range(self.instance.num_renewable):
                    time_res_profile[t][r] += req_r[r]

            solution.start_times[job] = start_time
            completion_times[job] = start_time + duration

        solution.makespan = completion_times[self.instance.num_jobs]
        solution.is_feasible = True
        return True