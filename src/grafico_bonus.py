import matplotlib.pyplot as plt
import os
import sys

def gerar_grafico_empilhado():
    caminho_raiz = os.path.join(os.getcwd(), "results", "Bonus", "Summary_Bonus.txt")
    caminho_src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results", "Bonus", "Summary_Bonus.txt")

    if os.path.exists(caminho_raiz):
        txt_path = caminho_raiz
        pasta_raiz_projeto= os.getcwd()
    elif os.path.exists(caminho_src):
        txt_path = caminho_src
        pasta_raiz_projeto = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    else:
        print("Erro: O ficheiro Summary_Bonus.txt não foi encontrado.")
        print(f"Tentei procurar em:\n1: {caminho_raiz}\n2: {caminho_src}")
        sys.exit(1)

    instancias = []
    cmax_valores = []
    extra_valores = []
    z_valores = []

    #Lê o ficheiro de texto
    with open(txt_path, 'r', encoding='utf-8') as f:
        linhas = f.readlines()

    #Processa apenas as linhas que contêm instâncias (.mm)
    for linha in linhas:
        if ".mm" in linha:
            partes = [p.strip() for p in linha.split('|')]

            nome_instancia = partes[0].replace(".mm", '')
            custo_z = float(partes[1])
            cmax = float(partes[2])
            custo_extra = float(partes[3])

            instancias.append(nome_instancia)
            cmax_valores.append(cmax)
            extra_valores.append(custo_extra)
            z_valores.append(custo_z)

    #Criação do gráfico
    fig, ax = plt.subplots(figsize=(10, 6))

    #Barra inferior: Makespan (Cmax)
    barras_cmax = ax.bar(instancias, cmax_valores, label='Makespan (Cmax)', color='#4C72B0', edgecolor='black')

    #Barra superior (empilhada): Custo Recursos Extra
    barras_extra = ax.bar(instancias, extra_valores, bottom=cmax_valores, label='Custo Recursos Extra', color='#DD8452', edgecolor='black')

    #Adiciona os rótulos de dados (Custo Total Z) no topo de cada barra
    for i, z in enumerate(z_valores):
        ax.text(i, z+1, f"Z={int(z)}", ha='center', va='bottom', fontweight='bold', color='black')

    #Estilo do gráfico
    ax.set_ylabel('Unidades (Tempo / Custo)')
    ax.set_title('Análise de Trade-Off (Tempo vs. Custo de Recursos Extra)', fontsize=14, fontweight='bold', pad=15)
    ax.legend(loc='upper left')
    ax.grid(axis='y', linestyle='--', alpha=0.7)

    plt.xticks(rotation=15)
    plt.tight_layout()

    target_dir_grafico = os.path.join(pasta_raiz_projeto, "Gantt_Charts", "TradeOffs")
    os.makedirs(target_dir_grafico, exist_ok=True)

    #Guarda a imagem na pasta results
    img_path = os.path.join(target_dir_grafico, "Grafico_Bonus_TradeOff.png")
    plt.savefig(img_path, dpi=300)

    plt.close()

    print(f"Gráfico gerado com sucesso em: {img_path}")

if __name__ == "__main__":
    gerar_grafico_empilhado()