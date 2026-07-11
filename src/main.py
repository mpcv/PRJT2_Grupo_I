import os
import time
from data_reader import Instance
from lineup import ScheduleBuilder
from data_writer import save_file_for_solution, save_summary_file
from visualizer import generate_gantt_chart
from tester import Tester
import random

def main():
    random.seed(0) #Garante a reprodutilidade nos testes

    #BKS conhecidos para estas instâncias

    bks_dict = {
        "10Jobs1.mm": 18,
        "10Jobs2.mm": 16,
        "20Jobs1.mm": 42,
        "20Jobs2.mm": 31,
        "30Jobs1.mm": 47
    }

    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(base_dir, "..", "input")

    print("\n--- A iniciar a Fase 1: Procedimento Construtivo ---")
    lista_resultados = []

    for root, dirs, files in os.walk(input_dir):
        for filename in sorted(files):
            if filename.endswith(".mm"):
                full_path = os.path.join(root, filename)
                print(f"\nA processar {filename}...")

                start = time.time()
                instance = Instance(full_path)
                builder = ScheduleBuilder(instance)
                best_sol = None

                #Gera várias para tentar apanhar uma inicial boa
                for _ in range(500):
                    sol = builder.gerar_solucao_inicial()
                    if not sol.is_feasible:
                        continue
                    if best_sol is None or sol.makespan < best_sol.makespan:
                        best_sol = sol
                
                #Verificação rigorosa
                tester = Tester(instance)
                is_valid = tester.verify_solution(best_sol)
                temp_exec = time.time() - start

                if best_sol and best_sol.is_feasible and is_valid:
                    print(f"-> Viável! Makespan: {best_sol.makespan}")

                    rpd = None
                    if filename in bks_dict:
                        bks = bks_dict[filename]
                        rpd = 100 * (best_sol.makespan - bks) / bks
                        print(f"-> RPD: {rpd:.2f}% (BKS: {bks})")

                    print(f"-> Tempo: {temp_exec:.4f}s")

                    #Guarda os txts e gráficos
                    save_file_for_solution(best_sol, filename)
                    generate_gantt_chart(best_sol, filename)

                    lista_resultados.append({
                        'Instance': filename,
                        'Makespan': best_sol.makespan,
                        'BKS': bks_dict.get(filename, "N/A"),
                        'RPD (%)': f"{rpd:.2f}" if rpd is not None else "N/A",
                        'Runtime (s)': f"{temp_exec:.4f}"
                    })
                else:
                    print("-> Falhou a gerar solução viável.")
    
    save_summary_file(lista_resultados)
    print("\n--- Fase 1 Concluída ---")

if __name__ == "__main__":
    main()

        