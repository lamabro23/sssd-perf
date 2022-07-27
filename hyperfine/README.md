# Generate plots

The parameters are:

- `--files` - a list of JSON files containing the data captured by hyperfine.
- `--output` - a file to store the plotted figure (default: figures/figure.png).
- `--two-graphs` - the default is to generate one graph comparing the data from different runs, this switch lets the script plot the data in separate graphs.

Example:

```bash
python evaluator.py --files json/new/10-requests.json json/old/10-requests.json --output figures/10-requests.png
```
