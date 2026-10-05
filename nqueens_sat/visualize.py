import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import numpy as np
from matplotlib.ticker import ScalarFormatter

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SAVE_DIRS = [
    os.path.join(SCRIPT_DIR, 'results', 'figures'),
    os.path.abspath(os.path.join(SCRIPT_DIR, '..', 'report', 'figures'))
]

def setup_aesthetics():
    """Configure global matplotlib styles for publication-ready charts."""
    plt.style.use('seaborn-v0_8-whitegrid')
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'axes.titlesize': 15,
        'axes.titleweight': 'bold',
        'axes.labelsize': 12,
        'axes.labelweight': 'bold',
        'xtick.labelsize': 11,
        'ytick.labelsize': 11,
        'legend.fontsize': 11,
        'legend.title_fontsize': 12,
        'figure.dpi': 300
    })

COLORS = {
    'BinomialEncoder': '#3498db',    # Blue
    'BinaryEncoder': '#2ecc71',      # Green
    'CommanderEncoder': '#9b59b6',   # Purple
    'SequentialEncoder': '#f39c12',  # Orange
    'ProductEncoder': '#e67e22',     # Dark Orange
    'ILP-PuLP-CBC': '#95a5a6',       # Light Gray
    'ILP-Gurobi': '#2c3e50',         # Navy
    'ILP-CPLEX': '#1abc9c',          # Teal
    'CP-CPLEX': '#f1c40f',           # Yellow
    'CP-SAT-ORTools': '#e74c3c',     # Red
    'Best SAT': '#27ae60',           # Dark Green
}

def load_results(csv_path=None):
    if csv_path is None:
        csv_path = os.path.join(SCRIPT_DIR, 'results', 'benchmark_results.csv')
    if not os.path.exists(csv_path):
        return None
    df = pd.read_csv(csv_path)
    df = df.replace(['TIMEOUT', 'inf', '-inf'], np.nan)
    for col in ['num_vars', 'num_clauses', 'num_aux_vars', 'encoding_time', 'solving_time', 'total_time']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.replace([np.inf, -np.inf], np.nan)
    return df

def _resolve_save_dirs(save_dir=None, save_dirs=None):
    dirs = save_dirs if save_dirs is not None else save_dir
    if dirs is None:
        target_list = list(DEFAULT_SAVE_DIRS)
    elif isinstance(dirs, str):
        target_list = [dirs]
    elif isinstance(dirs, (list, tuple, set)):
        target_list = list(dirs)
    else:
        target_list = list(DEFAULT_SAVE_DIRS)
    
    report_fig_dir = os.path.abspath(os.path.join(SCRIPT_DIR, '..', 'report', 'figures'))
    norm_report = os.path.normpath(report_fig_dir)
    
    unique_dirs = []
    seen = set()
    for d in target_list:
        norm = os.path.normpath(os.path.abspath(d))
        if norm not in seen:
            seen.add(norm)
            unique_dirs.append(norm)
            
    if norm_report not in seen:
        unique_dirs.append(norm_report)
        
    return unique_dirs

def _save_figure(fig, filename, save_dir=None, save_dirs=None):
    unique_dirs = _resolve_save_dirs(save_dir, save_dirs)
    for d in unique_dirs:
        os.makedirs(d, exist_ok=True)
        fig.savefig(os.path.join(d, f"{filename}.png"), bbox_inches='tight')
        fig.savefig(os.path.join(d, f"{filename}.pdf"), bbox_inches='tight')

def plot_solving_time_comparison(df, save_dir=None, save_dirs=None):
    fig = plt.figure(figsize=(12, 6))
    encoders = df['encoder_name'].unique()
    
    n_categories = sorted(df['n'].unique())
    
    for i, encoder in enumerate(encoders):
        data = df[df['encoder_name'] == encoder].dropna(subset=['solving_time']).sort_values('n')
        if data.empty: continue
        
        linestyle = '--' if 'ILP' in encoder else ':' if 'CP' in encoder else '-'
        marker = ['o', 's', '^', 'D', 'v', 'X', 'P', '*', 'H', 'd'][i % 10]
        
        plt.plot(data['n'], data['solving_time'], label=encoder, 
                 color=COLORS.get(encoder, '#333'), linestyle=linestyle, 
                 marker=marker, markersize=6, linewidth=2.0, alpha=0.85)
        
    plt.xscale('log')
    plt.yscale('log')
    
    plt.xticks(n_categories, [str(int(n)) for n in n_categories])
    
    plt.xlabel('Board Size (N) [Log Scale]')
    plt.ylabel('Solving Time (s) [Log Scale]')
    plt.title('Solving Time Comparison Across Approaches (Log-Log)')
    
    plt.grid(True, which="both", ls="--", alpha=0.5)
    plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left')
    plt.tight_layout()
    _save_figure(fig, "solving_time_comparison", save_dir=save_dir, save_dirs=save_dirs)
    plt.close(fig)

def plot_encoding_time(df, save_dir=None, save_dirs=None):
    fig = plt.figure(figsize=(10, 6))
    target_n = [10, 20, 30, 40]
    sub_df = df[df['n'].isin(target_n) & ~df['encoder_name'].str.contains('ILP|CP')].dropna(subset=['encoding_time'])
    if sub_df.empty:
        plt.close(fig)
        return
    
    sns.barplot(data=sub_df, x='n', y='encoding_time', hue='encoder_name', 
                palette=COLORS, edgecolor='white', linewidth=1.2)
    
    plt.xlabel('Board Size (N)')
    plt.ylabel('Encoding Time (s)')
    plt.title('Encoding Time Overhead by SAT Encoder')
    
    plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left', title='Method')
    plt.tight_layout()
    _save_figure(fig, "encoding_time_comparison", save_dir=save_dir, save_dirs=save_dirs)
    plt.close(fig)

def plot_variables_clauses(df, save_dir=None, save_dirs=None):
    sat_df = df[~df['encoder_name'].str.contains('ILP|CP', na=False)].dropna(subset=['num_vars', 'num_clauses'])
    if sat_df.empty: return
    
    fig, ax1 = plt.subplots(figsize=(12, 6))
    n_categories = sorted(sat_df['n'].unique())
    
    for i, encoder in enumerate(sat_df['encoder_name'].unique()):
        data = sat_df[sat_df['encoder_name'] == encoder].sort_values('n')
        c = COLORS.get(encoder, '#333')
        ax1.plot(data['n'], data['num_clauses'], marker='s', linestyle='-', color=c, 
                 linewidth=2.0, markersize=6, label=f'{encoder} (Clauses)')
        
    ax1.set_xscale('log')
    ax1.set_yscale('log')
    ax1.set_xticks(n_categories)
    ax1.set_xticklabels([str(int(n)) for n in n_categories])
    
    ax1.set_xlabel('Board Size (N) [Log Scale]')
    ax1.set_ylabel('Number of Clauses (Solid Lines)', color='#2c3e50', fontweight='bold')
    ax1.grid(True, which="both", ls="--", alpha=0.5)
    
    ax2 = ax1.twinx()
    for i, encoder in enumerate(sat_df['encoder_name'].unique()):
        data = sat_df[sat_df['encoder_name'] == encoder].sort_values('n')
        c = COLORS.get(encoder, '#333')
        ax2.plot(data['n'], data['num_vars'], marker='o', linestyle=':', color=c, 
                 linewidth=2.0, markersize=6, alpha=0.8, label=f'{encoder} (Vars)')
        
    ax2.set_yscale('log')
    ax2.grid(False) 
    
    plt.title('Formula Complexity: Variables vs Clauses Growth (Log-Log)')
    
    fig.legend(loc='upper center', bbox_to_anchor=(0.5, -0.01), ncol=3, frameon=True)
    plt.tight_layout()
    _save_figure(fig, "variables_clauses", save_dir=save_dir, save_dirs=save_dirs)
    plt.close(fig)

def plot_sat_vs_exact(df, save_dir=None, save_dirs=None):
    fig = plt.figure(figsize=(12, 6))
    sat_df = df[~df['encoder_name'].str.contains('ILP|CP', na=False)].dropna(subset=['total_time'])
    if sat_df.empty:
        plt.close(fig)
        return
    
    best_sat = sat_df.loc[sat_df.groupby('n')['total_time'].idxmin()].copy()
    best_sat['Method'] = 'Best SAT'
    
    exact_dfs = []
    exact_solvers = ['ILP-PuLP-CBC', 'ILP-Gurobi', 'ILP-CPLEX', 'CP-CPLEX', 'CP-SAT-ORTools']
    for solver in exact_solvers:
        s_df = df[df['encoder_name'] == solver].dropna(subset=['total_time']).copy()
        if not s_df.empty:
            s_df['Method'] = solver
            exact_dfs.append(s_df)
    
    combined = pd.concat([best_sat] + exact_dfs)
    target_n = [10, 20, 30, 40, 50, 75]
    sub_combined = combined[combined['n'].isin(target_n)]
    
    if not sub_combined.empty:
        sns.barplot(data=sub_combined, x='n', y='total_time', hue='Method', 
                    palette=COLORS, edgecolor='white', linewidth=1.2)
        plt.yscale('log')
        plt.xlabel('Board Size (N)')
        plt.ylabel('Total Time (s) [Log Scale]')
        plt.title('Benchmark: Best SAT vs Exact Methods')
        plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left', title='Solver Engine')
        plt.tight_layout()
        _save_figure(fig, "sat_vs_exact", save_dir=save_dir, save_dirs=save_dirs)
    plt.close(fig)

def plot_scalability_heatmap(df, save_dir=None, save_dirs=None):
    fig = plt.figure(figsize=(12, 7))
    pivot_df = df.pivot(index='encoder_name', columns='n', values='solving_time')
    
    sns.heatmap(pivot_df, annot=True, cmap='YlGnBu', fmt='.2f', 
                cbar_kws={'label': 'Solving Time (s)'},
                linewidths=0.5, linecolor='gray',
                mask=pivot_df.isnull(),
                annot_kws={"size": 10})
    
    plt.xlabel('Board Size (N)')
    plt.ylabel('Solver / Encoder')
    plt.title('Scalability Heatmap: Performance Matrix across N')
    plt.tight_layout()
    _save_figure(fig, "scalability_heatmap", save_dir=save_dir, save_dirs=save_dirs)
    plt.close(fig)

def plot_cactus(df, save_dir=None, save_dirs=None):
    """Plot Cactus Plot: Cumulative runtime vs number of solved instances."""
    fig = plt.figure(figsize=(12, 6))
    encoders = df['encoder_name'].unique()
    max_solved = 0
    
    for i, encoder in enumerate(encoders):
        data = df[(df['encoder_name'] == encoder) & (df['satisfiable'] == True)].dropna(subset=['total_time'])
        data = data[np.isfinite(data['total_time'])]
        if data.empty:
            continue
            
        sorted_times = np.sort(data['total_time'].values)
        cum_times = np.cumsum(sorted_times)
        num_solved = len(cum_times)
        max_solved = max(max_solved, num_solved)
        
        x = np.arange(1, num_solved + 1)
        linestyle = '--' if 'ILP' in encoder else ':' if 'CP' in encoder else '-'
        marker = ['o', 's', '^', 'D', 'v', 'X', 'P', '*', 'H', 'd'][i % 10]
        color = COLORS.get(encoder, '#333')
        
        plt.plot(x, cum_times, label=encoder, color=color,
                 linestyle=linestyle, marker=marker, markersize=6,
                 linewidth=2.0, alpha=0.85)
                 
    plt.yscale('log')
    if max_solved > 0:
        plt.xticks(np.arange(1, max_solved + 1))
    plt.xlabel('Number of Solved Instances (Sorted by Speed)', fontweight='bold')
    plt.ylabel('Cumulative Runtime (s) [Log Scale]', fontweight='bold')
    plt.title('Cactus Plot: Cumulative Runtime vs Solved Instances', fontweight='bold')
    plt.grid(True, which="both", ls="--", alpha=0.5)
    plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left')
    plt.tight_layout()
    _save_figure(fig, "cactus_plot", save_dir=save_dir, save_dirs=save_dirs)
    plt.close(fig)

def generate_all_plots(csv_path=None, save_dir=None, save_dirs=None):
    setup_aesthetics()
    
    resolved_dirs = _resolve_save_dirs(save_dir, save_dirs)
        
    df = load_results(csv_path)
    if df is not None:
        plot_solving_time_comparison(df, save_dirs=resolved_dirs)
        plot_encoding_time(df, save_dirs=resolved_dirs)
        plot_variables_clauses(df, save_dirs=resolved_dirs)
        plot_sat_vs_exact(df, save_dirs=resolved_dirs)
        plot_scalability_heatmap(df, save_dirs=resolved_dirs)
        plot_cactus(df, save_dirs=resolved_dirs)
        print("All optimized aesthetic plots (including Cactus Plot) generated successfully to both results/figures and report/figures.")

if __name__ == '__main__':
    csv_file = os.path.join(SCRIPT_DIR, 'results', 'benchmark_results.csv')
    generate_all_plots(csv_file)
