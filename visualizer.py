import matplotlib.pyplot as plt
import os

def generate_gantt_chart(solution, filename, target_folder="../Gantt_Charts"):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    target_dir = os.path.join(base_dir, target_folder)

    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize = (12,10), sharex=True, gridspec_kw={'height_ratios': [2,1]})

    colors = ['skyblue', 'lightgreen', 'salmon', 'gold', 'violet', 'orange']
    jobs = sorted(list(solution.start_times.keys()))

    for job in jobs:
        if job not in solution.modes: continue

        mode = solution.modes[job]
        start = solution.start_times[job]
        duration = solution.instance.modes_data[job][mode]['duration']

        if duration == 0:
            ax1.plot(start,job,marker='D',color='black',markersize=6)
            continue
        
        current_color = colors [mode % len(colors)]

        ax1.barh(y=job, width=duration, left=start, color=current_color, edgecolor='black', height=0.6)

        mid_x = start + (duration/2)
        ax1.text(mid_x, job, f"M{mode}", ha='center', va='center', color='black', fontsize=8)

    ax1.set_ylabel("Tarefas (Jobs)")
    ax1.set_title(f"Gráfico de Gantt - {filename} (Makespan: {solution.makespan})")

    if solution.instance.num_jobs >20:
        ax1.set_yticks(range(1, solution.instance.num_jobs + 1, 2))
    else:
        ax1.set_yticks(range(1, solution.instance.num_jobs + 1))
    
    ax1.grid(True, axis='x', linestyle='--', alpha=0.5)
    ax1.invert_yaxis()

    makespan = int(solution.makespan)
    num_res = solution.instance.num_renewable

    usage = [[0] * (makespan+1) for _ in range(num_res)]

    for job in jobs:
        if job not in solution.modes: continue
        mode = solution.modes[job]
        start = int(solution.start_times[job])
        duration = solution.instance.modes_data[job][mode]['duration']
        req_r = solution.instance.modes_data[job][mode]['R']

        for t in range(start, start+duration):
            if t <= makespan:
                for r in range (num_res):
                    usage[r][t] += req_r[r]
    
    res_colors = ['blue', 'red', 'green', 'purple']
    for r in range(num_res):
        color = res_colors[r % len(res_colors)]
        cap = solution.instance.res_capacities['R'][r]

        ax2.step(range(makespan+1), usage[r], where='post', label=f'Uso R{r+1}', color=color, alpha=0.8, linewidth=2)
        ax2.axhline(y=cap, color=color, linestyle='--', label=f'Max R{r+1} ({cap})', alpha=0.5)

    ax2.set_ylabel("Recursos")
    ax2.set_xlabel("Tempo (Makespan)")
    ax2.set_title("Perfil de Consumo (Recursos Renováveis)")

    if num_res > 0:
        ax2.legend(loc='upper right', fontsize=8, ncol=max(1,num_res))
    
    ax2.grid(True, linestyle='--',alpha=0.5)
    plt.tight_layout()

    file_path = os.path.normpath(os.path.join(target_dir, f"Gantt_{filename.replace('.mm','')}.png"))
    plt.savefig(file_path)
    plt.close()

    print(f"-> Gantt guardado em: {file_path}")