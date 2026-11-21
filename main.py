"""Explore real Palmer Penguins measurements with explicit missing-data handling."""
from resources import ensure_assets
ensure_assets()

from pathlib import Path
import json
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parent
OUT = BASE / 'outputs'
COLORS = {'Adelie': '#176b87', 'Chinstrap': '#df8f2d', 'Gentoo': '#5c9768'}


def main():
    OUT.mkdir(exist_ok=True)
    frame = pd.read_csv(BASE / 'data' / 'penguins.csv')
    expected = {'species', 'island', 'bill_length_mm', 'bill_depth_mm', 'flipper_length_mm', 'body_mass_g', 'sex', 'year'}
    assert set(frame.columns) == expected
    # Do not silently drop all rows missing sex when analyzing mass and flipper length.
    missing = frame.isna().sum().rename('missing_rows').to_frame()
    missing['missing_pct'] = missing['missing_rows'] / len(frame) * 100
    missing.to_csv(OUT / 'missing_values.csv')
    measurements = ['bill_length_mm', 'bill_depth_mm', 'flipper_length_mm', 'body_mass_g']
    summary = frame.groupby('species')[measurements].agg(['count', 'mean', 'median', 'std'])
    summary.to_csv(OUT / 'species_statistics.csv')
    frame.groupby(['species', 'island']).size().rename('count').to_csv(OUT / 'species_island_counts.csv')
    pair = frame.dropna(subset=['flipper_length_mm', 'body_mass_g'])
    correlations = {'pooled': float(pair.flipper_length_mm.corr(pair.body_mass_g))}
    for species, group in pair.groupby('species'):
        correlations[species] = float(group.flipper_length_mm.corr(group.body_mass_g))
    assert len(pair) + int(frame[['flipper_length_mm', 'body_mass_g']].isna().any(axis=1).sum()) == len(frame)
    result = {'rows': len(frame), 'species_counts': frame.species.value_counts().to_dict(),
              'rows_used_for_mass_flipper_plot': len(pair), 'total_missing_cells': int(frame.isna().sum().sum()),
              'mean_body_mass_g': frame.groupby('species').body_mass_g.mean().round(2).to_dict(),
              'pearson_r_mass_vs_flipper': correlations}
    (OUT / 'results.json').write_text(json.dumps(result, indent=2))
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.7))
    for species, group in pair.groupby('species'):
        axes[0].scatter(group.flipper_length_mm, group.body_mass_g, label=species, alpha=.7, s=22, color=COLORS[species])
    axes[0].set(title='Body size by species', xlabel='Flipper length (mm)', ylabel='Body mass (g)')
    axes[0].legend(fontsize=8)
    mass = [frame.loc[frame.species == s, 'body_mass_g'].dropna() for s in COLORS]
    boxes = axes[1].boxplot(mass, tick_labels=list(COLORS), patch_artist=True)
    for patch, color in zip(boxes['boxes'], COLORS.values()):
        patch.set_facecolor(color)
    axes[1].set(title='Mass distributions', ylabel='Body mass (g)')
    missing.missing_rows.plot.barh(ax=axes[2], color='#176b87')
    axes[2].set(title='Missing data audit', xlabel='Rows with missing value', ylabel='')
    fig.tight_layout()
    fig.savefig(OUT / 'penguins_dashboard.png', dpi=150)
    plt.close(fig)
    means = result['mean_body_mass_g']
    (OUT / 'report.md').write_text(f'''# Penguins findings

- {len(frame)} penguins across three species; {len(pair)} have both mass and flipper measurements.
- Mean body mass: Adelie {means['Adelie']:.0f} g, Chinstrap {means['Chinstrap']:.0f} g, Gentoo {means['Gentoo']:.0f} g.
- Pooled Pearson correlation (flipper length vs mass): {correlations['pooled']:.3f}.
- Within-species correlations: {', '.join(f'{s} {correlations[s]:.3f}' for s in COLORS)}.

The pooled association is stronger than some within-species associations. Species mix matters;
a pooled correlation is not a causal effect. Samples come from particular islands and years,
not a random sample of every penguin population. No claim of statistical significance is made.
Missing sex values are not imputed, and do not exclude otherwise usable mass/flipper pairs.
The counts in species_statistics.csv are per measurement, not an invented common denominator.

![Penguins dashboard](penguins_dashboard.png)
''')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
