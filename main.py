import json
import graphviz

GRAPH_ATTR = dict(ranksep='0.5', splines="ortho")
NODE_ATTR = dict(shape='box', width='2.3', height='0.6', fontname="Arial")
NODE_INTERMEDIATE_ATTR = dict(shape='none', width='0', height='0', label="")
EDGE_ATTR = dict(dir='none')

def print_node(node):
    node_id = node.get('id')
    node_name = node.get('name')
    node_shortName = node.get('shortName')

    print(f'{node_id} {node_name} ({node_shortName})')


def get_children(node):
    for edge in node['children']['edges']:
        yield edge['node']


def walk_children(node, node_function=None, level=0, graph=None):

    if not node.get('children'):
        return None

    i = 0
    prev_intermediate = None
    for edge in node['children']['edges']:
        child_node = edge['node']

        if node_function:
            node_function(child_node)

        if level < 3:
            graph.edge(node['id'], child_node['id'])
        else:
            intermediate = f"{node['id'][-5:]}_{child_node['id'][-5:]}_intermediate"
            graph.node(intermediate, **NODE_INTERMEDIATE_ATTR)

            if prev_intermediate:
                graph.edge(prev_intermediate, intermediate)
            else:
                graph.edge(node['id'], intermediate)

            with graph.subgraph(graph_attr={'rank': 'same'}) as c:
                c.edge(intermediate, child_node['id'])

            prev_intermediate = intermediate

        walk_children(child_node, node_function, level=level+1, graph=graph)
        i+=1


def main():
    f = open('organigramm.json')
    orga = json.load(f)

    root = orga['data']['organisationEntity']

    dot = graphviz.Digraph('BfDI',
                           comment='Bundesbeauftragter für den Datenschutz und die Informationsfreiheit (BfDI)',
                           )
    dot.graph_attr.update(GRAPH_ATTR)
    dot.node_attr.update(NODE_ATTR)
    dot.edge_attr.update(EDGE_ATTR)

    print_node(root)

    dot.node(root['id'], root['name'])

    def custom_node_function(node):
        print_node(node)

        # find headOf
        # we assert that there is only one headOf
        reverse_claims = map(lambda e: e['node'], node['reverseClaims']['edges'])
        head_of = next(filter(lambda n: n['claimType']['name'] == 'headOf', reverse_claims), None)

        if head_of:
            head_of_label = f"{head_of['entity']['position']} {head_of['entity']['name']}"
        else:
            head_of_label = 'NN'

        name_lines = ',<BR/>'.join(node['name'].split(', '))
        if node['shortName']:
            node_text = f"<<B>{node['shortName']}</B><BR/>{name_lines}<BR/><BR/>{head_of_label}>"
        else:
            node_text = f"<<B>{name_lines}</B><BR/><BR/>{head_of_label}>"

        dot.node(node['id'], node_text)

    walk_children(root, custom_node_function, graph=dot)

    print(dot.source)

    dot.format = 'png'
    dot.render(directory='output').replace('\\', '/')

if __name__ == '__main__':
    main()
