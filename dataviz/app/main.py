import streamlit as st
from PIL import Image
import seaborn as sns
from classes.visualize import create_pairplot, create_histogram, create_violinplot

# Load data
df = sns.load_dataset('iris')
attributes = df.columns[:-1].tolist()
species = df['species'].unique().tolist()

# page config
st.set_page_config(
    page_title="Test JEA",
    page_icon=":bar_chart:",
    layout="wide"
    )

st.title("Reporte Operacional Modalities RadioImagenes :bar_chart:")

# Expander
with st.expander("Detalle"):
    st.header("Report DICOM metadata")
    st.write("Test data jeam readioimagenes radiologos asociados santa  marta")
    main_top_image = Image.open("images/radiology_1.jpg")
    st.image(main_top_image)

# sidebar and filters
with st.sidebar:
    st.header("Filtros", divider=True)
    # dropdown para seleccionar atributos
    selected_attribute = st.selectbox("Attribute: ", attributes, index=0)
    # Multiselct
    selected_species = st.multiselect("Species: ", species, placeholder="Filtre por Especie")

# handle filter selections
if not selected_species:
    selected_species = species
filtered_df = df[df['species'].isin(selected_species)]

# descriptivas basicas
st.header("Estadigrafos")
st.dataframe(df.describe(), use_container_width=True)

# Plotly charts
st.header("DataViz")
# scatter plot
pairplot_fig = create_pairplot(filtered_df, attributes, selected_species)
st.plotly_chart(pairplot_fig, use_container_width=True)


# add columns
col1, col2 = st.columns(2)
# Histogram
with col1:
    hist_fig = create_histogram(filtered_df, selected_attribute)
    st.plotly_chart(hist_fig, use_container_width=True)
# Violin plot
with col2:
    show_points = st.checkbox("Show All Points in Violin Plot", value=True)
    violin_fig = create_violinplot(filtered_df, selected_attribute, points="all" if show_points else False)
    st.plotly_chart(violin_fig, use_container_width=True)




