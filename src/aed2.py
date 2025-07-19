import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import pandas as pd
from matplotlib.patches import Ellipse, Patch
import warnings
import os
import datetime

warnings.filterwarnings('ignore')

def load_gexf_file(file_path):
    """Carrega arquivo GEXF e retorna o grafo"""
    try:
        # Tenta carregar o arquivo GEXF
        G = nx.read_gexf(file_path)
        
        # Remove atributos problemáticos dos nós e arestas
        for node in G.nodes():
            # Remove atributos vazios ou problemáticos
            attrs_to_remove = []
            for attr, value in G.nodes[node].items():
                if value == '' or value is None:
                    attrs_to_remove.append(attr)
            for attr in attrs_to_remove:
                del G.nodes[node][attr]
        
        for edge in G.edges():
            # Remove atributos vazios ou problemáticos das arestas
            attrs_to_remove = []
            for attr, value in G.edges[edge].items():
                if value == '' or value is None:
                    attrs_to_remove.append(attr)
            for attr in attrs_to_remove:
                del G.edges[edge][attr]
        
        print(f"Grafo carregado com sucesso!")
        print(f"Número de nós: {G.number_of_nodes()}")
        print(f"Número de arestas: {G.number_of_edges()}")
        
        # Converte para grafo não direcionado se necessário
        if G.is_directed():
            print("Convertendo grafo direcionado para não direcionado...")
            G = G.to_undirected()
        
        return G
        
    except Exception as e:
        print(f"Erro ao carregar o arquivo: {e}")
        print("Tentando métodos alternativos de carregamento...")
        
        # Método alternativo 1: Carregar como MultiGraph
        try:
            G = nx.read_gexf(file_path, node_type=str)
            if G.is_multigraph():
                G = nx.Graph(G)  # Converte para grafo simples
            if G.is_directed():
                G = G.to_undirected()
            
            print(f"Grafo carregado com método alternativo!")
            print(f"Número de nós: {G.number_of_nodes()}")
            print(f"Número de arestas: {G.number_of_edges()}")
            return G
        except Exception as e2:
            print(f"Método alternativo 1 falhou: {e2}")
        
        # Método alternativo 2: Carregar linha por linha
        try:
            print("Tentando carregar manualmente...")
            import xml.etree.ElementTree as ET
            
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            G = nx.Graph()
            
            # Namespace do GEXF
            ns = {'gexf': 'http://www.gexf.net/1.2draft'}
            
            # Adiciona nós
            nodes = root.findall('.//gexf:node', ns)
            if not nodes:  # Tenta sem namespace
                nodes = root.findall('.//node')
            
            for node in nodes:
                node_id = node.get('id')
                if node_id:
                    G.add_node(node_id)
            
            # Adiciona arestas
            edges = root.findall('.//gexf:edge', ns)
            if not edges:  # Tenta sem namespace
                edges = root.findall('.//edge')
            
            for edge in edges:
                source = edge.get('source')
                target = edge.get('target')
                if source and target:
                    G.add_edge(source, target)
            
            print(f"Grafo carregado manualmente!")
            print(f"Número de nós: {G.number_of_nodes()}")
            print(f"Número de arestas: {G.number_of_edges()}")
            return G
            
        except Exception as e3:
            print(f"Método manual falhou: {e3}")
            return None

def analyze_degree_distribution(G, output_folder):
    """Análise da distribuição de graus com CDF e PDF, salvando em arquivos separados"""
    degrees = [G.degree(n) for n in G.nodes()]
    
    # Ajusta bins para lidar com casos de poucos graus
    if len(set(degrees)) > 1:
        bins = max(degrees) - min(degrees) + 1
    else:
        bins = 1 # Single bin if all degrees are the same

    # --- 1. Gráfico da Distribuição de Grau (PDF) ---
    fig1, ax1 = plt.subplots(1, 1, figsize=(10, 6))
    
    ax1.hist(degrees, bins=bins, 
             density=False, alpha=0.8, color='skyblue', 
             edgecolor='black', label='Count')
    
    ax1_twin = ax1.twinx()
    if len(degrees) > 1 and np.std(degrees) > 0: # Garante dados suficientes para KDE
        # Estende o range para uma curva mais suave e para cobrir os extremos
        x_smooth = np.linspace(min(degrees) - 1, max(degrees) + 1, 500) 
        kde = stats.gaussian_kde(degrees)
        pdf_smooth = kde(x_smooth)
        ax1_twin.plot(x_smooth, pdf_smooth, 'r-', linewidth=3, 
                      label='Probability Density Function (PDF)')
    
    ax1.set_xlabel('Degree')
    ax1.set_ylabel('Count', color='blue')
    ax1_twin.set_ylabel('Probability', color='red')
    ax1.set_title('Degree Distribution (PDF)')
    ax1.grid(True, alpha=0.3)
    
    # Legenda combinada para PDF
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax1_twin.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, 'degree_distribution_pdf.png'))
    plt.close(fig1) # Fecha a figura para liberar memória

    # --- 2. Gráfico da Função de Distribuição Cumulativa (CDF) ---
    fig2, ax2 = plt.subplots(1, 1, figsize=(10, 6))
    
    ax2.hist(degrees, bins=bins, 
             density=False, alpha=0.8, color='skyblue', 
             edgecolor='black', label='Count')
    
    ax2_twin = ax2.twinx()
    sorted_degrees = np.sort(degrees)
    y_cdf = np.arange(1, len(sorted_degrees) + 1) / len(sorted_degrees)
    
    # Ajusta o zorder para garantir que a linha vermelha não sobreponha a legenda
    ax2_twin.plot(sorted_degrees, y_cdf, 'r-', linewidth=3, 
                  label='Cumulative Density Function (CDF)', zorder=2) # zorder maior
    
    ax2.set_xlabel('Degree')
    ax2.set_ylabel('Count', color='blue')
    ax2_twin.set_ylabel('Probability', color='red')
    ax2.set_title('Cumulative Distribution Function (CDF)')
    ax2.grid(True, alpha=0.3)
    
    # Legenda combinada para CDF (ajusta a localização para evitar a curva)
    lines1, labels1 = ax2.get_legend_handles_labels()
    lines2, labels2 = ax2_twin.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper left') # Muda para upper left
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, 'degree_distribution_cdf.png'))
    plt.close(fig2) # Fecha a figura para liberar memória
    
    # Calcula percentis
    percentiles = [25, 50, 75]
    perc_values = np.percentile(degrees, percentiles)
    
    return perc_values

def calculate_centrality_metrics(G):
    """Calcula métricas de centralidade"""
    print("Calculando métricas de centralidade...")
    
    # Diferentes métricas de centralidade
    centrality_metrics = {}
    
    # Centralidade de grau
    centrality_metrics['degree'] = nx.degree_centrality(G)
    
    # Centralidade de proximidade
    if nx.is_connected(G):
        centrality_metrics['closeness'] = nx.closeness_centrality(G)
    else:
        # Para grafos desconectados, calcula por componente
        centrality_metrics['closeness'] = {}
        for component in nx.connected_components(G):
            subgraph = G.subgraph(component)
            closeness_sub = nx.closeness_centrality(subgraph)
            centrality_metrics['closeness'].update(closeness_sub)
    
    # Centralidade de intermediação
    centrality_metrics['betweenness'] = nx.betweenness_centrality(G)
    
    # Centralidade de autovetor
    try:
        centrality_metrics['eigenvector'] = nx.eigenvector_centrality(G, max_iter=1000)
    except nx.exception.PowerIterationFailedConvergence:
        print("Não foi possível calcular centralidade de autovetor (convergência falhou). Usando zeros.")
        centrality_metrics['eigenvector'] = {node: 0 for node in G.nodes()}
    except Exception as e:
        print(f"Erro ao calcular centralidade de autovetor: {e}. Usando zeros.")
        centrality_metrics['eigenvector'] = {node: 0 for node in G.nodes()}

    # PageRank
    try:
        centrality_metrics['pagerank'] = nx.pagerank(G)
    except Exception as e:
        print(f"Erro ao calcular PageRank: {e}. Usando zeros.")
        centrality_metrics['pagerank'] = {node: 0 for node in G.nodes()}
    
    return centrality_metrics

def multivariate_centrality_analysis(centrality_metrics, output_folder):
    """Análise multivariável das métricas de centralidade - Matriz de scatter plots"""
    # Converte para DataFrame
    df = pd.DataFrame(centrality_metrics)
    
    # Seleciona apenas as métricas principais
    metrics = ['betweenness', 'degree', 'eigenvector', 'closeness']
    df_selected = df[metrics]
    
    # Cria figura com subplots em grid
    fig, axes = plt.subplots(len(metrics), len(metrics), figsize=(16, 16))
    
    # Remove espaçamento entre subplots
    plt.subplots_adjust(hspace=0.1, wspace=0.1)
    
    for i, metric_y in enumerate(metrics):
        for j, metric_x in enumerate(metrics):
            ax = axes[i, j]
            
            # Remove bordas dos subplots para replicar o estilo da imagem
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['bottom'].set_visible(False)
            ax.spines['left'].set_visible(False)
            ax.set_facecolor('#f5f5f5') # Cor de fundo levemente cinza

            if i == j:
                # Diagonal: histograma da própria métrica com KDE
                values = df_selected[metric_x].values
                # Usar kdeplot para ter o mesmo estilo da imagem
                sns.kdeplot(values, ax=ax, color='red', fill=True, alpha=0.1, linewidth=2)
                ax.hist(values, bins=20, alpha=0.7, color='lightgray', 
                         density=True, edgecolor='gray') # Usar lightgray para barras

                # Define limites para o histograma na diagonal
                # CORREÇÃO: Usar np.ptp() em vez de values.ptp() para NumPy 2.0+
                ax.set_xlim(values.min() - 0.05 * np.ptp(values), values.max() + 0.05 * np.ptp(values))
                ax.set_ylim(bottom=0)
            else:
                # Fora da diagonal: scatter plot com elipses de densidade
                x_vals = df_selected[metric_x].values
                y_vals = df_selected[metric_y].values
                
                # Scatter plot com pontos menores e mais escuros, como na imagem
                ax.scatter(x_vals, y_vals, alpha=0.8, s=15, color='darkred', edgecolor='none')
                
                # Adiciona elipses de densidade
                if len(np.unique(x_vals)) > 1 and len(np.unique(y_vals)) > 1:
                    from matplotlib.patches import Ellipse
                    from scipy.stats import chi2
                    
                    data = np.column_stack([x_vals, y_vals])
                    mean = np.mean(data, axis=0)
                    cov = np.cov(data.T)
                    
                    if not np.all(np.isclose(cov, 0)): # Evita erro com matriz de covariância nula
                        eigenvals, eigenvecs = np.linalg.eigh(cov)
                        order = eigenvals.argsort()[::-1]
                        eigenvals = eigenvals[order]
                        eigenvecs = eigenvecs[:, order]
                        
                        angle = np.degrees(np.arctan2(eigenvecs[1, 0], eigenvecs[0, 0]))
                        
                        # Desenha elipses para diferentes níveis de confiança, como na imagem
                        for confidence, color, alpha in [(0.5, 'darkred', 0.2), (0.9, 'red', 0.1)]:
                            chi2_val = chi2.ppf(confidence, df=2)
                            width = 2 * np.sqrt(chi2_val * eigenvals[0])
                            height = 2 * np.sqrt(chi2_val * eigenvals[1])
                            
                            ellipse = Ellipse(mean, width, height, angle=angle, 
                                              facecolor=color, alpha=alpha, edgecolor='darkred', linewidth=1)
                            ax.add_patch(ellipse)
                
            # Configuração dos eixos
            if i == len(metrics) - 1:  # Última linha: rótulos do eixo X
                ax.set_xlabel(metric_x.capitalize(), fontsize=10, fontweight='bold')
                ax.tick_params(axis='x', labelsize=8)
            else:
                ax.set_xticklabels([])
            
            if j == 0:  # Primeira coluna: rótulos do eixo Y
                ax.set_ylabel(metric_y.capitalize(), fontsize=10, fontweight='bold')
                ax.tick_params(axis='y', labelsize=8)
            else:
                ax.set_yticklabels([])
            
            # Remove ticks menores
            ax.tick_params(axis='both', which='minor', length=0)
            ax.tick_params(axis='both', which='major', length=3) # Mantém ticks maiores para alinhamento
            
            # Adiciona pequenas linhas para os ticks, como na imagem
            ax.tick_params(axis='x', direction='out', length=4, width=0.5, colors='gray')
            ax.tick_params(axis='y', direction='out', length=4, width=0.5, colors='gray')

            # Remova o grid para replicar a imagem
            ax.grid(False) 
    
    plt.suptitle('Multivariate Centrality Analysis', fontsize=20, fontweight='bold', y=0.98) # Ajusta posição do título
    plt.tight_layout(rect=[0, 0, 1, 0.96]) # Ajusta layout para o suptitle
    plt.savefig(os.path.join(output_folder, 'multivariate_centrality_analysis.png'))
    plt.close(fig) # Fecha a figura para liberar memória
    
    return df_selected

def identify_peripheral_and_central_nodes(G, centrality_metrics, top_n=10):
    """Identifica vértices na periferia e centro da rede"""
    
    # Combina métricas para criar um score geral
    combined_scores = {}
    
    for node in G.nodes():
        score = 0
        count = 0
        for metric_name, metric_values in centrality_metrics.items():
            if node in metric_values and not np.isnan(metric_values[node]):
                score += metric_values[node]
                count += 1
        combined_scores[node] = score / count if count > 0 else 0
    
    # Ordena os nós por score
    sorted_nodes = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
    
    # Identifica nós centrais e periféricos
    central_nodes = sorted_nodes[:top_n]
    peripheral_nodes = sorted_nodes[-top_n:]
    
    print(f"\n=== CENTRALITY AND PERIPHERY ANALYSIS ===")
    print(f"\nTOP {top_n} CENTRAL NODES:")
    for i, (node, score) in enumerate(central_nodes, 1):
        print(f"{i}. Node {node}: Score = {score:.4f}")
    
    print(f"\nTOP {top_n} PERIPHERAL NODES:")
    for i, (node, score) in enumerate(peripheral_nodes, 1):
        print(f"{i}. Node {node}: Score = {score:.4f}")
    
    # Análise por métrica individual
    print(f"\n=== ANALYSIS BY INDIVIDUAL METRIC ===")
    for metric in centrality_metrics:
        sorted_metric = sorted(centrality_metrics[metric].items(), 
                               key=lambda x: x[1], reverse=True)
        print(f"\n{metric.upper()} - Top 5:")
        for i, (node, value) in enumerate(sorted_metric[:5], 1):
            print(f"   {i}. Node {node}: {value:.4f}")
    
    return central_nodes, peripheral_nodes, combined_scores

def visualize_network_with_centrality(G, combined_scores, central_nodes, peripheral_nodes, output_folder):
    """Visualiza a rede destacando nós centrais e periféricos e salva a imagem"""
    
    plt.figure(figsize=(16, 12))
    
    try:
        # Layout da rede
        print("Calculating network layout...")
        pos = nx.spring_layout(G, k=0.5, iterations=50) # Ajuste 'k' para espaçamento entre nós
        
        # Cores dos nós baseadas no score
        node_colors = []
        node_sizes = []
        
        central_node_ids = [node for node, score in central_nodes]
        peripheral_node_ids = [node for node, score in peripheral_nodes]
        
        # Verifica se os nós existem no grafo
        valid_central = [node for node in central_node_ids if node in G.nodes()]
        valid_peripheral = [node for node in peripheral_node_ids if node in G.nodes()]
        
        for node in G.nodes():
            if node in valid_central:
                node_colors.append('red')
                node_sizes.append(300)
            elif node in valid_peripheral:
                node_colors.append('blue')
                node_sizes.append(200)
            else:
                node_colors.append('lightgray')
                node_sizes.append(100)
        
        # Desenha a rede
        print("Drawing edges...")
        nx.draw_networkx_edges(G, pos, alpha=0.3, width=0.5, edge_color='gray')
        
        print("Drawing nodes...")
        nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes, alpha=0.8)
        
        # Adiciona rótulos apenas para nós centrais e periféricos (limitado para evitar poluição visual)
        important_nodes_labels = {}
        for node_id, score in central_nodes[:5]: # Top 5 central nodes
            if node_id in pos:
                important_nodes_labels[node_id] = f"C-{str(node_id)[:6]}"
        for node_id, score in peripheral_nodes[:5]: # Top 5 peripheral nodes
            if node_id in pos:
                important_nodes_labels[node_id] = f"P-{str(node_id)[:6]}"

        if important_nodes_labels:
            print("Adding labels...")
            nx.draw_networkx_labels(G, pos, labels=important_nodes_labels, 
                                    font_size=8, font_weight='bold', font_color='black')
        
        plt.title('Network with Highlighted Central (Red) and Peripheral (Blue) Nodes', 
                  fontsize=16, fontweight='bold')
        
        # Legenda
        legend_elements = [
            Patch(facecolor='red', label=f'Central Nodes ({len(valid_central)})'),
            Patch(facecolor='blue', label=f'Peripheral Nodes ({len(valid_peripheral)})'),
            Patch(facecolor='lightgray', label='Other Nodes')
        ]
        plt.legend(handles=legend_elements, loc='upper right')
        
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(os.path.join(output_folder, 'network_centrality_visualization.png'))
        plt.close() # Fecha a figura
        
    except Exception as e:
        print(f"Error in visualization: {e}")
        print("Attempting simplified visualization...")
        
        # Visualização mais simples em caso de erro
        plt.figure(figsize=(12, 8))
        
        # Layout mais simples
        pos = nx.random_layout(G)
        
        # Desenha apenas os nós com cores
        node_colors = []
        for node in G.nodes():
            if node in [n for n, s in central_nodes]:
                node_colors.append('red')
            elif node in [n for n, s in peripheral_nodes]:
                node_colors.append('blue')
            else:
                node_colors.append('lightgray')
        
        nx.draw(G, pos, node_color=node_colors, node_size=50, 
                 alpha=0.8, with_labels=False, edge_color='gray', width=0.5)
        
        plt.title('Simplified Network Visualization', fontsize=14)
        plt.axis('off')
        plt.savefig(os.path.join(output_folder, 'simplified_network_visualization.png'))
        plt.close() # Fecha a figura

def main():
    """Função principal"""
    print("=== NETWORK ANALYSIS - REQUIREMENT 3 ===\n")
    
    # Cria uma pasta única para cada execução com timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_folder = f"network_analysis_results_{timestamp}"
    os.makedirs(output_folder, exist_ok=True)
    print(f"Results will be saved in: '{output_folder}'")

    # Procura arquivos GEXF na pasta atual
    gexf_files = [f for f in os.listdir('.') if f.endswith('.gexf')]
    
    if gexf_files:
        print(f"GEXF files found: {gexf_files}")
        file_path = gexf_files[0]  # Usa o primeiro arquivo encontrado
        print(f"Using file: {file_path}")
    else:
        print("No GEXF file found in the current folder.")
        file_path = input("Enter the full path to the GEXF file: ")
    
    # Carrega o grafo
    G = load_gexf_file(file_path)
    
    if G is None:
        print("Error: Could not load the file.")
        print("Please check if:")
        print("1. The file exists at the specified path")
        print("2. The file is in a valid GEXF format")
        print("3. The file is not corrupted")
        return
    
    # Verifica se o grafo não está vazio
    if G.number_of_nodes() == 0:
        print("Error: The graph has no nodes.")
        return
    
    if G.number_of_edges() == 0:
        print("Warning: The graph has no edges. Some centrality metrics might be zero or undefined.")
        # Pode continuar com a análise de centralidade de grau, mas outras métricas serão zero.
    
    print("\n1. Analyzing degree distribution...")
    percentiles = analyze_degree_distribution(G, output_folder)
    
    print("\n2. Calculating centrality metrics...")
    centrality_metrics = calculate_centrality_metrics(G)
    
    print("\n3. Performing multivariate analysis...")
    df_centrality = multivariate_centrality_analysis(centrality_metrics, output_folder)
    
    print("\n4. Identifying central and peripheral nodes...")
    central_nodes, peripheral_nodes, combined_scores = identify_peripheral_and_central_nodes(
        G, centrality_metrics, top_n=10
    )
    
    print("\n5. Visualizing the network...")
    visualize_network_with_centrality(G, combined_scores, central_nodes, peripheral_nodes, output_folder)
    
    print("\n=== ANALYSIS COMPLETED ===")
    print(f"Degree distribution percentiles: 25%={percentiles[0]:.1f}, 50%={percentiles[1]:.1f}, 75%={percentiles[2]:.1f}")

if __name__ == "__main__":
    main()
