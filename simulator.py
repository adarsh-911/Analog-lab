import streamlit as st
import graphviz
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class Component:
    type: str
    value: float
    unit: str
    node1: int = 0
    node2: int = 0
    
    def get_label(self) -> str:
        if self.type == 'G':
            return "Ground"
        return f"{self.type}: {self.value} {self.unit}"
    
    def get_symbol(self) -> str:
        symbols = {
            'R': 'R',
            'L': 'L',
            'C': 'C',
            'G': '⏚'
        }
        return symbols.get(self.type, '─○─')

@dataclass
class FilterBlock:
    name: str
    position: int
    parent_id: Optional[str] = None
    block_id: Optional[str] = None
    components: Dict[str, List[Component]] = None
    sub_blocks: List['FilterBlock'] = None
    start_node: int = 0
    end_node: int = 0

    def __post_init__(self):
        if self.components is None:
            self.components = {component_type: [] for component_type in COMPONENTS.keys()}
        if self.sub_blocks is None:
            self.sub_blocks = []
        if self.block_id is None:
            self.block_id = f"block_{id(self)}"

    def add_component(self, component_type: str, value: float, unit: str):
        if component_type in self.components:
            self.components[component_type].append(Component(component_type, value, unit))

    def remove_component(self, component_type: str, index: int):
        if component_type in self.components and 0 <= index < len(self.components[component_type]):
            self.components[component_type].pop(index)

    def add_sub_block(self, block: 'FilterBlock'):
        block.parent_id = self.block_id
        self.sub_blocks.append(block)
        self.sub_blocks.sort(key=lambda x: x.position)

    def remove_sub_block(self, block_id: str):
        self.sub_blocks = [b for b in self.sub_blocks if b.block_id != block_id]
        for idx, block in enumerate(self.sub_blocks):
            block.position = idx

COMPONENTS = {
    'C': {'name': 'Capacitor', 'units': ['pF', 'nF', 'µF', 'mF']},
    'L': {'name': 'Inductor', 'units': ['nH', 'µH', 'mH', 'H']},
    'R': {'name': 'Resistor', 'units': ['Ω', 'kΩ', 'MΩ']},
    'G': {'name': 'Ground', 'units': ['-']}
}

class FilterTopology:
    def __init__(self, name: str):
        self.name = name
        self.blocks: List[FilterBlock] = []
        self.next_node = 1

    def add_block(self, block: FilterBlock):
        self.blocks.append(block)
        self.blocks.sort(key=lambda x: x.position)

    def remove_block(self, block_id: str):
        self.blocks = [b for b in self.blocks if b.block_id != block_id]
        for idx, block in enumerate(self.blocks):
            block.position = idx

    def generate_netlist(self) -> str:
        """Generate a SPICE-like netlist for the entire topology."""
        netlist = [f"* Netlist for {self.name}"]
        component_count = 1
        self.next_node = 1
        
        def process_block(block: FilterBlock, input_node: int) -> int:
            nonlocal component_count
            block.start_node = input_node
            current_node = input_node
            
            # Process parallel components
            parallel_start_node = current_node
            max_parallel_node = current_node
            
            for comp_type, components in block.components.items():
                for comp in components:
                    if comp_type == 'G':
                        netlist.append(f"V{component_count} {current_node} 0 GND")
                    else:
                        next_node = self.next_node
                        self.next_node += 1
                        comp.node1 = parallel_start_node
                        comp.node2 = next_node
                        netlist.append(f"{comp.type}{component_count} {parallel_start_node} {next_node} {comp.value}{comp.unit}")
                        max_parallel_node = max(max_parallel_node, next_node)
                    component_count += 1
            
            current_node = max_parallel_node
            block.end_node = current_node
            
            # Process sub-blocks
            for sub_block in block.sub_blocks:
                current_node = process_block(sub_block, current_node)
            
            return current_node

        # Process all top-level blocks
        current_node = 1
        for block in self.blocks:
            current_node = process_block(block, current_node)

        return "\n".join(netlist)

def create_circuit_visualization(topology: FilterTopology) -> graphviz.Digraph:
    graph = graphviz.Digraph()
    graph.attr(rankdir='LR')
    
    def process_block(block: FilterBlock, parent_node=None):
        with graph.subgraph(name=f'cluster_{block.block_id}') as s:
            s.attr(label=block.name)
            s.attr(style='rounded')
            
            in_node = f"{block.block_id}_in"
            out_node = f"{block.block_id}_out"
            s.node(in_node, "", shape='point')
            s.node(out_node, "", shape='point')
            
            junction_in = f"{block.block_id}_junction_in"
            junction_out = f"{block.block_id}_junction_out"
            s.node(junction_in, "", shape='point')
            s.node(junction_out, "", shape='point')
            
            s.edge(in_node, junction_in)
            s.edge(junction_out, out_node)
            
            has_components = False
            for comp_type, components in block.components.items():
                for idx, comp in enumerate(components):
                    comp_node = f"{block.block_id}_{comp_type}_{idx}"
                    
                    if comp_type == 'G':
                        s.node(comp_node, "⏚", shape='plain')
                        s.edge(junction_in, comp_node)
                    else:
                        label = f"{comp_type}\n{comp.value}{comp.unit}"
                        s.node(comp_node, label, shape='box', style='filled', fillcolor='lightblue')
                        s.edge(junction_in, comp_node)
                        s.edge(comp_node, junction_out)
                        has_components = True
            
            if not has_components:
                s.edge(junction_in, junction_out)
            
            for sub_block in block.sub_blocks:
                sub_in, sub_out = process_block(sub_block, out_node)
                graph.edge(out_node, sub_in)
            
            return in_node, out_node
    
    graph.node('input', 'IN', shape='diamond')
    graph.node('output', 'OUT', shape='diamond')
    
    prev_node = 'input'
    for block in topology.blocks:
        block_in, block_out = process_block(block)
        graph.edge(prev_node, block_in)
        prev_node = block_out
    
    graph.edge(prev_node, 'output')
    
    return graph

def create_default_topologies() -> Dict[str, FilterTopology]:
    return {
        'Custom': FilterTopology('Custom'),
        'T-Network': FilterTopology('T-Network'),
        'Pi-Network': FilterTopology('Pi-Network'),
        'Ladder Network': FilterTopology('Ladder Network')
    }

def render_block_components(block: FilterBlock, block_key: str):
    st.write("Components in this block:")
    
    for component_type, info in COMPONENTS.items():
        st.subheader(f"{info['name']}s")
        
        for idx, component in enumerate(block.components[component_type]):
            cols = st.columns([3, 2, 1])
            with cols[0]:
                if component_type == 'G':
                    st.write(f"Ground {idx + 1}")
                else:
                    st.write(f"{component.type} {idx + 1}: {component.value} {component.unit}")
            with cols[2]:
                if st.button(f"Remove {component.type} {idx + 1}", key=f"remove_{block_key}_{component_type}_{idx}"):
                    block.remove_component(component_type, idx)
                    st.rerun()
        
        cols = st.columns([2, 2, 2, 1])
        with cols[0]:
            if component_type != 'G':
                value = st.number_input(f"New {info['name']} Value", min_value=0.0, format="%f", key=f"value_{block_key}_{component_type}")
            else:
                value = 0.0
        with cols[1]:
            unit = st.selectbox(f"Unit", info['units'], key=f"unit_{block_key}_{component_type}")
        with cols[2]:
            if st.button(f"Add {component_type}", key=f"add_{block_key}_{component_type}"):
                block.add_component(component_type, value, unit)
                st.rerun()

def render_circuit_view(topology):
    st.header('Circuit Visualization')
    if topology.blocks:
        circuit_graph = create_circuit_visualization(topology)
        st.graphviz_chart(circuit_graph)
    else:
        st.write("Add blocks to see the circuit visualization")

def main():
    st.title('Filter Topology Designer')
    
    if 'topologies' not in st.session_state:
        st.session_state.topologies = create_default_topologies()
    if 'current_topology' not in st.session_state:
        st.session_state.current_topology = None
    if 'block_counter' not in st.session_state:
        st.session_state.block_counter = 0

    topology_names = list(st.session_state.topologies.keys())
    selected_topology = st.selectbox(
        'Select Filter Topology',
        topology_names,
        key='topology_selector'
    )

    if selected_topology != st.session_state.current_topology:
        st.session_state.current_topology = selected_topology
        st.session_state.block_counter = len(st.session_state.topologies[selected_topology].blocks)

    topology = st.session_state.topologies[selected_topology]
    
    st.header('Manage Blocks')
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Add New Block")
        new_block_name = st.text_input("Block Name", value=f"Block {st.session_state.block_counter + 1}")
        parent_options = ["None"] + [f"{block.name} ({block.block_id})" for block in topology.blocks]
        parent_block = st.selectbox("Parent Block", parent_options)
        
        if st.button("Add Block"):
            new_block = FilterBlock(new_block_name, st.session_state.block_counter)
            if parent_block == "None":
                topology.add_block(new_block)
            else:
                parent_id = parent_block.split("(")[1].rstrip(")")
                for block in topology.blocks:
                    if block.block_id == parent_id:
                        block.add_sub_block(new_block)
                        break
            st.session_state.block_counter += 1
            st.rerun()
    
    with col2:
        st.subheader("Remove Block")
        if topology.blocks:
            blocks_to_remove = []
            for block in topology.blocks:
                blocks_to_remove.append(f"{block.name} ({block.block_id})")
                for sub_block in block.sub_blocks:
                    blocks_to_remove.append(f"  ↳ {sub_block.name} ({sub_block.block_id})")
            
            block_to_remove = st.selectbox("Select Block", blocks_to_remove)
            if st.button("Remove Selected Block"):
                block_id = block_to_remove.split("(")[1].rstrip(")")
                topology.remove_block(block_id)
                for block in topology.blocks:
                    block.remove_sub_block(block_id)
                st.session_state.block_counter -= 1
                st.rerun()

    if topology.blocks:
        st.header(f'Configure {selected_topology}')
        
        all_blocks = []
        for block in topology.blocks:
            all_blocks.append((block, 0))
            for sub_block in block.sub_blocks:
                all_blocks.append((sub_block, 1))
        
        tabs = st.tabs([f"{'  ' * level}{block.name}" for block, level in all_blocks])
        
        for tab, (block, _) in zip(tabs, all_blocks):
            with tab:
                st.subheader(block.name)
                render_block_components(block, block.block_id)
        
        render_circuit_view(topology)

        st.header('Circuit Netlist')
        netlist = topology.generate_netlist()
        st.text_area("SPICE-like Netlist", netlist, height=200)

        if st.button('Export Netlist'):
            st.download_button(
                label='Download Netlist',
                data=netlist,
                file_name='circuit.sp',
                mime='text/plain'
            )

if __name__ == '__main__':
    main()