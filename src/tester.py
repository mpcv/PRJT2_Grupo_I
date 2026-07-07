class Tester:
    def __init__(self, instance):
        self.instance = instance
    
    def verify_solution(self, solution):
        is_valid = True

        #1. Verifica as precedências
        for job in range(1, self.instance.num_jobs + 1):
            if job not in solution.start_times: continue
            for pred in self.instance.predecessors.get(job, []):
                if pred not in solution.start_times: continue
                pred_mode = solution.modes[pred]
                end_pred = solution.start_times[pred] + self.instance.modes_data[pred][pred_mode]['duration']
                if solution.start_times[job] < end_pred:
                    print(f"Erro precedência: Job {job} começa às {solution.start_times[job]} mas o pai {pred} acaba às {end_pred}")
                    is_valid = False
            
        #2. Verifica N resources (orçamento global)
        total_n = [0] * self.instance.num_nonrenewable
        for job, mode in solution.modes.items():
            if job in self.instance.modes_data:
                req_n = self.instance.modes_data[job][mode]['N']
                for i in range(self.instance.num_nonrenewable):
                    total_n[i] += req_n[i]

        for i in range(self.instance.num_nonrenewable):
            if total_n[i] > self.instance.res_capacities['N'][i]:
                print(f"Erro cap N{i+1}: Gastou {total_n[i]} mas o max era {self.instance.res_capacities['N'][i]}")
                is_valid = False

        #3. Verifica R resources (minuto a minuto)
        makespan = int(solution.makespan)
        for t in range(makespan):
            usage_r = [0] * self.instance.num_renewable
            active_jobs = []

            for job, start in solution.start_times.items():
                if job not in self.instance.modes_data: continue
                mode = solution.modes[job]
                dur = self.instance.modes_data[job][mode]['duration']

                #Se a tarefa está a decorrer neste instante
                if start <= t < start + dur:
                    active_jobs.append(job)
                    req_r = self.instance.modes_data[job][mode]['R']
                    for r in range(self.instance.num_renewable):
                        usage_r[r] += req_r[r]

            for r in range(self.instance.num_renewable):
                if usage_r[r] > self.instance.res_capacities['R'][r]:
                    print(f"Erro cap R{r+1} no min {t}: Gastou {usage_r[r]} > Max {self.instance.res_capacities['R'][r]}. Jobs ativos: {active_jobs}")
                    is_valid = False

        return is_valid