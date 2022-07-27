# Generate plots

The parameters are:

- `--files` - a list of CSV files containing the data captured by SystemTap.
- `--output` - a file to store the plotted figure (default: figures/figure.png).
- `--scatterplot` - the default is to generate a boxplot comparing the data from different runs (or to plot a single run), this switch lets the script plot the data in separate scatterplots.

Example:

```bash
python evaluator.py --files csv/new/750-requests.csv --files csv/old/750-requests.csv --output figures/10-requests.png
```
