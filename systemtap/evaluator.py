import argparse
import csv
from pathlib import Path

from matplotlib.lines import Line2D
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
import seaborn as sns


def output(name: str) -> str:
    parent_dir = Path(name).parent
    if not parent_dir.exists():
        parent_dir.mkdir(parents=True, exist_ok=True)
    return name

parser = argparse.ArgumentParser()
parser.add_argument('-f', '--files', nargs='+', type=str)
parser.add_argument('-o', '--output', type=output, default='figures/figure.png')
parser.add_argument('--scatterplot', action='store_true')
args = parser.parse_args()


def transpose_csv(file: str, new_file: Path) -> None:
    og = zip(*csv.reader(open(file, 'r')))
    csv.writer(open(new_file, 'w')).writerows(og)

non_user = 'wrong@ipa.test'
my_palette = ['#fb4d3d', '#345995']
props = dict(marker='o', mec='black', mfc='w')

# Transpose the values in CSV files, save them to a new one
df = []
for x in args.files:
    p = Path(x)
    new_name = p.with_name('fixed_' + p.name)
    transpose_csv(x, new_name)
    df.append(pd.read_csv(new_name))

# Get rid of the largest and lowest outliers for clearer plots
# Inspired by:
# https://stackoverflow.com/questions/23199796/detect-and-exclude-outliers-in-a-pandas-dataframe
new_df = []
for f in df:
    new_df.append(f[(np.abs(stats.zscore(f)) < 3).all(axis=1)])

col_names = df[0].columns.values

data = pd.concat(new_df, keys=['new', 'old'], names=['version', 'req_num'])
data = pd.melt(data.reset_index(), id_vars=['req_num', 'version'],
               value_vars=data.columns.tolist(), var_name='provider',
               value_name='time', ignore_index=False)

data['time'] = data['time'].div(1000)

plt.rc('legend', loc="upper right")
sns.set_palette(palette=my_palette)

if args.scatterplot:
    custom_legend = [Line2D([0], [0], color='black', label='Mean'),
                     Line2D([0], [0], color='black', label='Median', linestyle='--'),
                     Line2D([0], [0], color='black', label='Q1', linestyle=':'),
                     Line2D([0], [0], color='black', label='Q3', linestyle='-.')]

    fig, axes = plt.subplots(len(col_names), 1, figsize=(18/2.54, 3*(28/2.54)))

    for ax, name in zip(axes, col_names):
        ax.set_xlabel('Num. of request')
        ax.set_ylabel('Time (us)')
        ax.title.set_text(name)

        ax.grid(axis='y', alpha=0.8, linewidth=0.5)

        curr = data.loc[data.provider == name].reset_index()
        sns.scatterplot(ax=ax, data=curr, x=curr.req_num, y=curr.time, hue=curr.version, s=8)
        handles, labels = ax.get_legend_handles_labels()
        for i, vrsn in enumerate(curr.version.unique()):
            sep_vrsn = curr.loc[curr.version == vrsn]
            ax.axhline(sep_vrsn.time.mean(), color=my_palette[i])
            ax.axhline(sep_vrsn.time.median(), color=my_palette[i], linestyle='--')
            ax.axhline(sep_vrsn.time.quantile(0.25, interpolation='midpoint'),
                       color=my_palette[i], linestyle=':')
            ax.axhline(sep_vrsn.time.quantile(0.75, interpolation='midpoint'),
                       color=my_palette[i], linestyle='-.')

        ax.add_artist(ax.legend(handles, labels, loc='upper right'))
        ax.legend(handles=custom_legend, loc='upper left')
else:
    # Separate data into two dataframes if error values were measured too
    g = data.groupby('provider')
    if non_user in g.groups:
        error_data = g.get_group(non_user)
        data = data[data['provider'] != non_user]

    fig, ax = plt.subplots(1, 1, figsize=(18/2.54, 28/3/2.54))
    fig.suptitle(Path(args.files[0]).stem.split('-', 1)[0]
                 + ' requests per responder')

    boxplot = sns.boxplot(ax=ax, data=data, x='provider', y='time',
                          hue='version', hue_order=['old', 'new'],
                          flierprops=props)

    boxplot.set_xlabel('Provider name')
    boxplot.set_ylabel('Time (ms)')
    boxplot.grid(axis='y', alpha=0.8, linewidth=0.5)


plt.tight_layout()

if args.output:
    plt.savefig(args.output)

plt.show()

if not args.scatterplot:
    try:
        fig, ax = plt.subplots(1, 1, figsize=(18/2.54, 28/3/2.54))

        fig.suptitle(Path(args.files[0]).stem.split('-', 1)[0]
                     + ' requests for a non-existent user: wrong@ipa.test ')

        boxplot = sns.boxplot(ax=ax, data=error_data, x='provider', y='time',
                              hue='version', hue_order=['old', 'new'],
                              flierprops=props)
        boxplot.set_xlabel(f'User: {error_data.provider.unique()[0]}')
        boxplot.set_ylabel('Time (ms)')
        boxplot.grid(axis='y', alpha=0.8, linewidth=0.5)

        ax.get_xaxis().set_ticks([])
        plt.tight_layout()

        if args.output:
            plt.savefig(args.output[:-4] + '-error' + args.output[-4:])

        plt.show()
    except NameError:
        print('No error data was measured')
