import os
import time
import random
from data_reader import Instance
from lineup import ScheduleBuilder
from data_writer import save_file_for_solution, save_summary_file, save_schedule_csv, save_bonus_summary_files
from visualizer import generate_gantt_chart
from tester import Tester
from metaheuristic import SimulatedAnnealing
from bonus_solver import BonusScheduleBuilder, BonusSimulatedAnnealing
from grafico_bonus import gerar_grafico_empilhado

def main():
    random.seed(42) #Garante a reprodutilidade nos testes

    print("\n--- Otimização MRCPSP | Grupo I ---")
    print("1 - Projeto Principal (Minizar Tempo)")
    print("2 - Desafio de Valorização (Minimizar Custo)")
    modo_execucao = input("Opção (1 ou 2):").strip()
    is_bonus = (modo_execucao == '2')

    bks_dict = {
        "10Jobs1.mm": 18,
        "10Jobs2.mm": 16,
        "20Jobs1.mm": 42,
        "20Jobs2.mm": 31,
        "30Jobs1.mm": 47
    }

    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(base_dir, "..", "input")

    print("\n--- A iniciar Otimização MRCPSP (Fase 1 e Fase 2) ---")
    lista_resultados = []

    SA_TIME_LIMIT = 60

    for root, dirs, files in os.walk(input_dir):
        for filename in sorted(files):
            if filename.endswith(".mm"):
                full_path = os.path.join(root, filename)
                print(f"\n[{filename}] A processar...")

                start = time.time()
                instance = Instance(full_path)

                #Instância Dinâmica dependendo do modo escolhido
                if is_bonus:
                    builder = BonusScheduleBuilder(instance)
                else:
                    builder = ScheduleBuilder(instance)

                best_initial_sol = None

                #Fase 1: Heurísitica Construtiva Inicial
                for _ in range(500):
                    sol = builder.gerar_solucao_inicial()
                    if not sol.is_feasible:
                        continue

                    custo_atual = sol.bonus_objective if is_bonus else sol.makespan
                    custo_melhor = best_initial_sol.bonus_objective if best_initial_sol and is_bonus else (best_initial_sol.makespan if best_initial_sol else float('inf'))
                    
                    if best_initial_sol is None or custo_atual < custo_melhor:
                        best_initial_sol = sol

                if not best_initial_sol or not best_initial_sol.is_feasible:
                    print("  -> [ERRO] Falhou ao gerar solução inicial viável.")
                    continue
                
                metrica_f1 = best_initial_sol.bonus_objective if is_bonus else best_initial_sol.makespan
                print(f"  -> [Fase 1] Solução inicial (Custo/Makespan): {metrica_f1}")

                #Fase 2: Simulated Annealing 
                bks = bks_dict.get(filename, None)

                if is_bonus:
                    sa = BonusSimulatedAnnealing(
                        instance, 
                        builder, 
                        initial_temp=150.0, 
                        cooling_rate=0.99, 
                        iterations_per_temp=150
                    )
                else:
                    sa = SimulatedAnnealing(
                        instance, 
                        builder, 
                        initial_temp=150.0, 
                        cooling_rate=0.99, 
                        iterations_per_temp=150
                    )


                #Executa o SA usando a melhor solução inicial como ponto de partida
                best_sa_sol, history = sa.run(
                    initial_solution=best_initial_sol,
                    time_limit=SA_TIME_LIMIT,
                    target_makespan=bks if not is_bonus else None
                )       

                #Verificação rigorosa
                tester = Tester(instance)
                is_valid = True

                #No modo bónus, ultrapassar a capacidade não invalida a solução
                if not is_bonus:
                    is_valid = tester.verify_solution(best_sa_sol)

                temp_exec = time.time() - start
                metrica_final = best_sa_sol.bonus_objective if is_bonus else best_sa_sol.makespan

                if best_sa_sol.is_feasible and is_valid:
                    print(f"  -> [Fase 2] Solução SA Otimizada: {metrica_final}")

                    #Calcular RPDs para as duas fases
                    rpd_fase1 = None
                    rpd_fase2 = None

                    if not is_bonus and bks is not None:
                        rpd_fase1 = 100 * (best_initial_sol.makespan - bks) / bks
                        rpd_fase2 = 100 * (best_sa_sol.makespan - bks) / bks
                        print(f"  -> RPD Fase 1: {rpd_fase1:.2f}% | RPD Fase 2: {rpd_fase2:.2f}% (BKS: {bks})")

                    print(f"  -> Tempo Total: {temp_exec:.4f}s")

                    #Guarda os txts, gráficos e csv
                    save_file_for_solution(best_sa_sol, filename)
                    generate_gantt_chart(best_sa_sol, filename)
                    
                    termination_reason = "bks_reached" if (not is_bonus and best_sa_sol.makespan == bks) else "time_limit"

                    save_schedule_csv(
                        solution=best_sa_sol,
                        filename=filename,
                        runtime=temp_exec,
                        algorithm="simulated_annealing",
                        seed=42,
                        termination=termination_reason
                    )

                    if is_bonus:
                        custo_extra = best_sa_sol.bonus_objective - best_sa_sol.makespan
                        lista_resultados.append({
                            'Instance': filename,
                            'Total_Cost': best_sa_sol.bonus_objective,
                            'Makespan': best_sa_sol.makespan,
                            'Extra_Cost': custo_extra,
                            'Runtime': f"{temp_exec:.4f}"
                        })
                    else:
                        lista_resultados.append({
                            'Instance': filename,
                            'BKS': bks if (bks is not None and not is_bonus) else "N/A",
                            'Mk_P1': best_initial_sol.bonus_objective if is_bonus else best_initial_sol.makespan,
                            'RPD_P1': f"{rpd_fase1:.2f}" if rpd_fase1 is not None else "N/A",
                            'Mk_P2': metrica_final,
                            'RPD_P2': f"{rpd_fase2:.2f}" if rpd_fase2 is not None else "N/A",
                            'Runtime (s)': f"{temp_exec:.4f}"
                        })
                else:
                    print("  -> [ERRO] A solução do SA violou restrições.")
    
    if is_bonus:
        save_bonus_summary_files(lista_resultados)
    else:
        save_summary_file(lista_resultados)
    
    print("\n--- Otimização Concluída. Resultados atualizados em 'results/'. ---")
    
    if is_bonus:
        gerar_grafico_empilhado()

if __name__ == "__main__":
    main()