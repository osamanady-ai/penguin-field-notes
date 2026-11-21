"""Interactive ecology explorer. Run: python -m streamlit run dashboard.py"""
from resources import ensure_assets
ensure_assets()

from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title='Penguin Field Notes', page_icon='🐧', layout='wide')
from design import setup, header, metrics, section, insight
setup('ecology')
header('ecology')

@st.cache_data
def load():
    return pd.read_csv(Path(__file__).parent / 'data' / 'penguins.csv')

frame = load()
st.sidebar.header('Filter the field sample')
species = st.sidebar.multiselect('Species', sorted(frame.species.unique()), default=sorted(frame.species.unique()))
islands = st.sidebar.multiselect('Islands', sorted(frame.island.unique()), default=sorted(frame.island.unique()))
years = st.sidebar.multiselect('Years', sorted(frame.year.unique()), default=sorted(frame.year.unique()))
sexes = st.sidebar.multiselect('Sex (Unknown includes missing)', ['female','male','Unknown'], default=['female','male','Unknown'])
view = frame.loc[frame.species.isin(species) & frame.island.isin(islands) & frame.year.isin(years) & frame.sex.fillna('Unknown').isin(sexes)].copy()
if view.empty:
    st.warning('No penguins match the filters. Select more species, islands, years or sex categories.')
    st.stop()
metrics(['Penguins in view','Mean mass','Mean flipper length','Missing cells'],
        [str(len(view)), f'{view.body_mass_g.mean():,.0f} g', f'{view.flipper_length_mm.mean():.1f} mm', str(view.isna().sum().sum())],
        ['bird','scale','ruler','layers'])
insight('Available observations only. Means use measured values; missing cells include sex. No measurements are imputed.')
explore, distributions, relationships, quality = st.tabs(['◈  Explore measurements','▥  Distributions','◎  Correlations','◇  Data & methods'])
measurements=['bill_length_mm','bill_depth_mm','flipper_length_mm','body_mass_g']
colors={'Adelie':'#0d9488','Chinstrap':'#e9a438','Gentoo':'#7478d3'}
with explore:
    section("Morphology explorer", "bird")
    left,right=st.columns(2)
    x=left.selectbox('Horizontal measurement',measurements,index=2)
    y=right.selectbox('Vertical measurement',measurements,index=3)
    pair=view.dropna(subset=list(set([x,y]))).copy()
    pair['sex'] = pair['sex'].fillna('Unknown')
    st.plotly_chart(px.scatter(pair,x=x,y=y,color='species',symbol='sex',hover_data=['island','year'],color_discrete_map=colors,title='Individual measurements',height=480),width='stretch',theme=None)
    st.caption(f'{len(pair)} records have both selected measurements. Missing sex is shown as Unknown in this chart.')
    counts=view.groupby(['island','species']).size().rename('count').reset_index()
    st.plotly_chart(px.bar(counts,x='island',y='count',color='species',barmode='group',color_discrete_map=colors,title='Sample counts by island and species'),width='stretch',theme=None)
with distributions:
    section("Compare the distributions", "layers")
    variable=st.selectbox('Measurement',measurements,index=3)
    left,right=st.columns(2)
    left.plotly_chart(px.box(view,x='species',y=variable,color='species',points='all',color_discrete_map=colors,title='Spread and individual values'),width='stretch',theme=None)
    right.plotly_chart(px.histogram(view,x=variable,color='species',barmode='overlay',opacity=.65,color_discrete_map=colors,title='Distribution by species',nbins=25),width='stretch',theme=None)
    st.dataframe(view.groupby('species')[measurements].agg(['count','mean','median','std']).round(2),width='stretch')
with relationships:
    section("Look beyond the pooled correlation", "target")
    corr=view[measurements].corr()
    st.plotly_chart(px.imshow(corr,zmin=-1,zmax=1,color_continuous_scale='RdBu_r',text_auto='.2f',title='Pearson correlation, pairwise complete observations'),width='stretch',theme=None)
    counts=view[measurements].notna().astype(int).T.dot(view[measurements].notna().astype(int))
    st.caption('Available pairs for each correlation (small filtered groups can be unstable):')
    st.dataframe(counts)
    rows=[]
    for label,group in [('All selected',view),*list(view.groupby('species'))]:
        pair=group[['flipper_length_mm','body_mass_g']].dropna()
        rows.append({'group':label,'n':len(pair),'mass_flipper_r':pair.iloc[:,0].corr(pair.iloc[:,1]) if len(pair)>1 else float('nan')})
    st.dataframe(pd.DataFrame(rows),hide_index=True)
    st.warning('Correlation is not causation. Pooled and within-species relationships differ. Island/species sampling is not balanced; do not treat group averages as experimental effects.')
with quality:
    section("Field data, with its gaps", "shield")
    missing=view.isna().sum().rename('missing_rows').rename_axis('column').reset_index()
    st.plotly_chart(px.bar(missing,x='column',y='missing_rows',title='Missing-value audit for selected records'),width='stretch',theme=None)
    st.dataframe(view,hide_index=True)
    st.download_button('Download filtered penguins',view.to_csv(index=False).encode('utf-8'),'filtered_penguins.csv','text/csv')
    st.markdown('''No fabricated measurements or model-generated rows. Per-chart missing rows are excluded only for the measurements needed. Counts per species and measurement are reported. Sample covers three species in 2007-2009, not all penguins.

Source and CC0 data credit: [Horst, Hill and Gorman, palmerpenguins](https://github.com/allisonhorst/palmerpenguins). Measurements: Kristen Gorman and Palmer Station LTER.''')
st.caption('Portfolio learning project · Hover, zoom, legend toggles and chart downloads available in Plotly controls')
