import argparse
import csv

from pathlib import Path
from matplotlib.lines import Line2D
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
import seaborn as sns


non_user = 'wrong@ipa.test'


def transpose_csv(file: str, new_file: Path) -> None:
    og = zip(*csv.reader(open(file, 'r')))
    csv.writer(open(new_file, 'w')).writerows(og)


def check_parent_dir(arg: str):
    p = Path(arg).parent
    if not p.exists():
        p.mkdir()
    return arg


parser = argparse.ArgumentParser()
parser.add_argument('-f', '--files', nargs='+', type=str,
                    default=['csv/stap.csv', 'csv/old_stap.csv'])
parser.add_argument('-o', '--output', type=lambda x: check_parent_dir(x),
                    default='figures/figure.png')
parser.add_argument('--scatterplot', action='store_true')
args = parser.parse_args()

props = dict(marker='o', mec='black', mfc='w')

df = []
for x in args.files:
    p = Path(x)
    new_name = p.with_name('fixed_' + p.name)
    transpose_csv(x, new_name)
    df.append(pd.read_csv(new_name))

new_df = []
for f in df:
    new_df.append(f[(np.abs(stats.zscore(f)) < 3).all(axis=1)])

assert len(new_df[0].columns.values) == len(new_df[1].columns.values)

col_names = df[0].columns.values

data = pd.concat(new_df, keys=['new', 'old'], names=['version', 'req_num'])
data = pd.melt(data.reset_index(), id_vars=['req_num', 'version'],
               value_vars=data.columns.tolist(), var_name='provider',
               value_name='time', ignore_index=False)

data['time'] = data['time'].div(1000)

plt.rc('legend', loc="upper right")

my_palette = ['#fb4d3d', '#345995']
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
