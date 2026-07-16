import os

def save_file_for_solution(solution,filename):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base_dir, "..", "results")

    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
    
    file_path = os.path.join(results_dir, f"Result_{filename.replace('.mm', '.txt')}")

    with open(file_path, "w", encoding='utf-8') as f:
        f.write(f"Instance: {filename}\n")
        f.write(f"Makespan: {solution.makespan}\n")
        f.write("-" * 35 + "\n")

        f.write(f"{'Job':<6} | {'Mode':<6} | {'Start':<6} | {'End':<6}\n")
        f.write("-" * 35 + "\n")

        sorted_jobs = sorted(solution.start_times.keys(), key=lambda x: solution.start_times[x])

        for job in sorted_jobs:
            if job in solution.modes:
                mode = solution.modes[job]
                start = solution.start_times[job]
                duration = solution.instance.modes_data[job][mode]['duration']
                end_time = start + duration

                f.write(f"{job:<6} | {mode:<6} | {start:<6} | {end_time:<6}\n")

def save_schedule_csv(solution, filename, runtime, algorithm="simulated_annealing", seed=42, termination="time_limit"):
    base_dir=os.path.dirname(os.path.abspath(__file__))
    results_dir=os.path.join(base_dir, "..", "results" )

    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
    
    instance_name = filename.replace('.mm', '')
    file_path = os.path.join(results_dir, f"schedule_{instance_name}.csv")

    with open (file_path, "w", encoding='utf-8') as f:
        f.write(f"# instance={instance_name}\n")
        f.write(f"# runtime_seconds={runtime:.2f}\n")
        f.write(f"# algorithm={algorithm}\n")
        f.write(f"# seed={seed}\n")
        f.write(f"# termination={termination}\n")
        f.write(f"activity_id,mode,start_time\n")

        sorted_jobs = sorted(solution.start_times.keys())

        for job in sorted_jobs:
            if job in solution.modes:
                mode = solution.modes[job]
                start = solution.start_times[job]
                f.write(f"{job},{mode},{start}\n")

def save_summary_file(results_list):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base_dir, "..", "results")

    if not os.path.exists(results_dir):
        os.makedirs(results_dir)

    path = os.path.join(results_dir, "Summary_Results.txt")

    with open(path, "w", encoding='utf-8') as f:
        f.write(f"{'Instance':<15}| {'BKS':<6}| {'Mk_P1':<8}| {'RPD_P1(%)':<10}| {'Mk_P2':<8}| {'RPD_P2(%)':<10}| {'Runtime(s)':<10}\n")
        f.write("-" * 80 + "\n")

        for res in results_list:
            f.write(f"{res['Instance']:<15}| {res['BKS']:<6}| {res['Mk_P1']:<8}| {res['RPD_P1']:<10}| {res['Mk_P2']:<8}| {res['RPD_P2']:<10}| {res['Runtime (s)']:<10}\n")

        valid_rpds = [float(res['RPD_P2']) for res in results_list if res['RPD_P2'] != "N/A"]
        if valid_rpds:
            avg_rpd = sum(valid_rpds) / len(valid_rpds)
            f.write("-" * 80 + "\n")
            f.write(f"{'Média Global':<15}| {'-':<6}| {'-':<8}| {'-':<10}| {'-':<8}| {avg_rpd:<10.2f}| {'-':<10}\n")