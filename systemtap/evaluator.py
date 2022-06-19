import argparse
import csv

from matplotlib.lines import Line2D
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
import seaborn as sns


providers = ['ipa.test', 'samba.test', 'ldap.test']


def transpose_csv(file: str, new_file: str) -> None:
    og = zip(*csv.reader(open(file, 'r')))
    csv.writer(open(new_file, 'w')).writerows(og)


parser = argparse.ArgumentParser()
parser.add_argument('-p', '--providers', nargs='+', default=providers)
parser.add_argument('-f', '--files', type=list, default=['stap.csv', 'old_stap.csv'])
args = parser.parse_args()


df = []
for x in args.files:
    transpose_csv(x, 'fixed_' + x)
    df.append(pd.read_csv('fixed_' + x))

# Remove outliers from the dataframes
df[0] = df[0][(np.abs(stats.zscore(df[0])) < 3).all(axis=1)]
df[1] = df[1][(np.abs(stats.zscore(df[1])) < 3).all(axis=1)]

assert len(df[0].columns.values) == len(df[1].columns.values)

col_names = df[0].columns.values

data = pd.concat(df, keys=['new', 'old'], names=['version', 'req_num'])
data = pd.melt(data.reset_index(), id_vars=['req_num', 'version'], value_vars=data.columns.tolist(), var_name='provider', value_name='time', ignore_index=False)

plt.rc('legend', loc="upper right")

my_palette = ['#fb4d3d', '#345995']
sns.set_palette(palette=my_palette)
fig, axes = plt.subplots(len(col_names), 1, figsize=(18/2.54, 3*(28/2.54)))
# fig.suptitle('Performance results')

custom_legend = [Line2D([0], [0], color='black', label='Mean'),
                 Line2D([0], [0], color='black', label='Median', linestyle='--')]

for ax, name in zip(axes, col_names):
    ax.set_xlabel('Num. of request')
    ax.set_ylabel('Time (us)')
    ax.title.set_text(name)

    ax.grid(axis='y', alpha=0.8, linewidth=0.5)

    curr = data.loc[data.provider == name].reset_index()
    sns.scatterplot(ax=ax, data=curr, x=curr.req_num, y=curr.time, hue=curr.version, s=8)
    handles, labels = ax.get_legend_handles_labels()
    for vrsn in curr.version.unique():
        sep_vrsn = curr.loc[curr.version == vrsn]
        sns.lineplot(ax=ax, data=sep_vrsn, x=sep_vrsn.req_num, y=sep_vrsn.time.mean(), hue=curr.version, linewidth=2)
        sns.lineplot(ax=ax, data=sep_vrsn, x=sep_vrsn.req_num, y=sep_vrsn.time.median(), hue=curr.version, linewidth=2, ls='--')

    ax.get_legend().remove()

fig.add_artist(fig.legend(handles, labels, loc='lower right'))
fig.legend(handles=custom_legend, loc='lower left')
plt.tight_layout()

plt.savefig('/home/duradnik/Tmp/figure.png')
plt.show()

# graph.axhline(df['ipa.test'].min())
# graph.axhline(df['ipa.test'].max())
# graph.axhline(df['ipa.test'].quantile(0.25, interpolation='midpoint'))
# graph.axhline(df['ipa.test'].quantile(0.75, interpolation='midpoint'))
