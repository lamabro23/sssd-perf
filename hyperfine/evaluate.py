import argparse
import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
import seaborn as sns


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('-f', '--files', nargs='+', type=str)
parser.add_argument('-t', '--title', type=str)
parser.add_argument('-o', '--output', type=str)
parser.add_argument('--one-graph', action='store_true')

args = parser.parse_args()

cmp = True if len(args.files) > 1 else False

results = []
for file in args.files:
    with open(file) as f:
        results.append(json.load(f)['results'])

dfs = []
for result in results:
    tmp_df = pd.DataFrame(dict(zip([res.get('command') for res in result],
                                   [res.get('times') for res in result])))
    tmp_df = tmp_df[(np.abs(stats.zscore(tmp_df)) < 4).all(axis=1)]

    if not args.one_graph:
        tmp_df = tmp_df.melt(var_name='command', value_name='time')
    dfs.append(tmp_df)


if args.one_graph:
    fig, ax = plt.subplots(1, 1, figsize=(18/2.54, 28/2.54))
    props = dict(marker='o', mec='black', mfc='w')

    if cmp:
        df = pd.concat(dfs, keys=['old', 'new'], names=['version', 'req_num'])
        df = pd.melt(df.reset_index(), id_vars=['req_num', 'version'],
                     var_name='command', value_name='time',
                     value_vars=df.columns.tolist())

        boxplot = sns.boxplot(ax=ax, data=df, x='command', y='time',
                              hue='version', flierprops=props)
        boxplot.set_xticklabels(boxplot.get_xticklabels(), rotation=30)
    else:
        df = pd.melt(dfs[0], var_name='command', value_name='time')
        boxplot = sns.boxplot(ax=ax, data=df, x='command', y='time',
                              hue='command', flierprops=props, dodge=False)
        boxplot.set_xticklabels([i + 1 for i in range(df['command'].nunique())])

    boxplot.set_ylabel('Time [s]')
    boxplot.set_xlabel('Commands')
    boxplot.legend()

else:
    fig, axes = plt.subplots(1, len(args.files), sharey=True,
                             figsize=(28/2.54, 18/2.54))

    if cmp:
        for file, (df, ax) in enumerate(zip(dfs, axes)):
            sns.boxplot(ax=ax, data=df, x='command',
                        y='time', hue='command', dodge=False)
            ax.set_xticklabels([i + 1 for i in range(df['command'].nunique())])
            ax.set_ylabel('Time [s]')
            ax.set_xlabel('Commands')
            ax.set_title(args.files[file])
            ax.legend()
    else:
        boxplot = sns.boxplot(ax=axes, data=dfs[0], x='command',
                              y='time', hue='command', dodge=False)
        boxplot.set_xticklabels(
                [i + 1 for i in range(dfs[0]['command'].nunique())])
        boxplot.set_ylabel('Time [s]')
        boxplot.set_xlabel('Commands')
        boxplot.legend()


fig.suptitle(args.title if args.title else 'Hyperfine benchmark of SSSD')
plt.tight_layout()

if args.output:
    plt.savefig(args.output)

plt.show()
