import plotly.express as px

def create_pairplot(df, attributes, species):
    fig = px.scatter_matrix(df, dimensions=attributes, color="species", 
                            opacity=0.6)
    fig.update_traces(diagonal_visible=False)
    return fig


def create_histogram(df, attribute):
    fig = px.histogram(df, x=attribute, color="species", marginal="box", barmode='overlay', opacity=0.7)
    fig.update_traces(marker=dict(line=dict(width=1, color='DarkSlateGrey')))
    fig.update_layout(title=f'Histogram of {attribute}', hovermode="x unified")
    fig.update_layout(bargap=0.1)
    return fig

def create_violinplot(df, attribute, points="all"):
    fig = px.violin(df, x="species", y=attribute, color="species", box=True, points=points, hover_data=df.columns)
    fig.update_layout(title=f'Violinplot of {attribute}', hovermode="x unified")
    return fig

def create_boxplot(df, attribute):
    fig = px.box(df, x="species", y=attribute, color="species", points="all", hover_data=df.columns)
    fig.update_layout(title=f'Boxplot of {attribute}', hovermode="x unified")
    return fig

def create_correlation_heatmap(df, attributes):
    corr = df[attributes].corr()
    fig = px.imshow(corr, text_auto=True, aspect="auto", color_continuous_scale='RdBu_r', title='Correlation Heatmap')
    return fig

def create_scatter_plot(df, x_attr, y_attr):
    fig = px.scatter(df, x=x_attr, y=y_attr, color="species", hover_data=df.columns, title=f'Scatter Plot of {x_attr} vs {y_attr}')
    return fig

def create_line_plot(df, x_attr, y_attr):
    fig = px.line(df, x=x_attr, y=y_attr, color="species", markers=True, title=f'Line Plot of {x_attr} vs {y_attr}')
    return fig

def create_pie_chart(df, attribute):
    fig = px.pie(df, names=attribute, title=f'Pie Chart of {attribute}')
    return fig

def create_bar_chart(df, x_attr, y_attr):
    fig = px.bar(df, x=x_attr, y=y_attr, color="species", barmode='group', title=f'Bar Chart of {y_attr} by {x_attr}')
    return fig

def create_area_chart(df, x_attr, y_attr):
    fig = px.area(df, x=x_attr, y=y_attr, color="species", title=f'Area Chart of {y_attr} by {x_attr}')
    return fig  

def create_facet_plot(df, x_attr, y_attr):
    fig = px.scatter(df, x=x_attr, y=y_attr, color="species", facet_col="species", title=f'Facet Plot of {y_attr} by {x_attr}')
    return fig  

def create_density_heatmap(df, x_attr, y_attr):
    fig = px.density_heatmap(df, x=x_attr, y=y_attr, nbinsx=20, nbinsy=20, title=f'Density Heatmap of {y_attr} vs {x_attr}')
    return fig
