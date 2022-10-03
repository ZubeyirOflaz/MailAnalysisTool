from pyvis.network import Network


def visualize_network(pandas_df, weight_limit):
    weighted_connections = pandas_df.groupby(['Sender', 'Recipient']).size().reset_index()
    weighted_connections.rename(columns={0: 'Weight'}, inplace=True)

    filter = weighted_connections['Weight'] > weight_limit

    filtered_df = weighted_connections[filter]

    pynetwork = Network(height='1080px', width='100%', bgcolor='#222222', font_color='white')

    # set the physics layout of the network

    sources = filtered_df['Sender']
    targets = filtered_df['Recipient']
    weights = filtered_df['Weight']

    edge_data = zip(sources, targets, weights)

    for e in edge_data:
        src = e[0]
        dst = e[1]
        w = e[2]

        pynetwork.add_node(src, src, title=src)
        pynetwork.add_node(dst, dst, title=dst)
        pynetwork.add_edge(src, dst, value=w)

    neighbor_map = pynetwork.get_adj_list()

    # add neighbor data to node hover data
    for node in pynetwork.nodes:
        node['title'] += ' Neighbors:<br>' + '<br>'.join(neighbor_map[node['id']])
        node['value'] = len(neighbor_map[node['id']])
    return pynetwork
