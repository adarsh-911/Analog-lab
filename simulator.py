import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import time
import schemdraw
import schemdraw.elements as elm
from dataclasses import dataclass
from typing import Optional, Tuple, List

@dataclass
class CircuitComponent:
    enabled: bool
    value: Optional[float] = None

@dataclass
class RLCNetwork:
    resistance: CircuitComponent
    inductance: CircuitComponent
    capacitance: CircuitComponent
    wire: CircuitComponent

def calculate_parallel_impedance(network: RLCNetwork, omega: float) -> complex:
    """
    Calculate complex impedance of RLC components in parallel
    
    Args:
        network: RLCNetwork object containing component values
        omega: Angular frequency in radians/second
    
    Returns:
        Complex impedance value
    """
    try:
        # Convert units to base SI
        L = network.inductance.value / 1000 if network.inductance.enabled else 0
        C = network.capacitance.value / 1e6 if network.capacitance.enabled else 0
        R = network.resistance.value if network.resistance.enabled else 0
        
        total_conductance = 0
        
        # Add conductances for enabled components
        if network.resistance.enabled and R > 0:
            total_conductance += 1/R
        if network.inductance.enabled and L > 0:
            total_conductance += 1/(1j * omega * L)
        if network.capacitance.enabled and C > 0 and omega != 0:
            total_conductance += 1j * omega * C
            
        return 1 / total_conductance if total_conductance != 0 else float('inf')
    except ZeroDivisionError:
        return float('inf')

def transfer_function(network1: RLCNetwork, network2: RLCNetwork, freq: float) -> complex:
    """
    Calculate transfer function of the two-port network
    
    Args:
        network1: Input network RLC components
        network2: Output network RLC components
        freq: Frequency in Hz
    
    Returns:
        Complex transfer function value
    """
    omega = 2 * np.pi * freq
    Z1 = calculate_parallel_impedance(network1, omega)
    Z2 = calculate_parallel_impedance(network2, omega)
    
    # Enhanced error handling for special cases
    if any(np.isclose([abs(Z1), abs(Z2)], 0, atol=1e-10)):
        return 0
    if abs(Z1) == float('inf') and abs(Z2) == float('inf'):
        return 1
    if abs(Z1) == float('inf'):
        return 1
    if abs(Z2) == float('inf'):
        return 0
        
    H = Z2 / (Z1 + Z2)
    return np.clip(H, -1e6, 1e6)  # Limit gain for numerical stability

def plot_frequency_response(network1: RLCNetwork, network2: RLCNetwork, 
                          freq_range: Tuple[float, float]) -> Tuple[np.ndarray, List[float], List[float]]:
    """Generate frequency response plot with enhanced error handling"""
    frequencies = np.logspace(np.log10(freq_range[0]), np.log10(freq_range[1]), 1000)
    gain = []
    phase = []
    
    for f in frequencies:
        H = transfer_function(network1, network2, f)
        if np.isfinite(H) and H != 0:
            gain.append(20 * np.log10(abs(H)))
            phase.append(np.angle(H, deg=True))
        else:
            gain.append(-120)
            phase.append(0)
    
    return frequencies, gain, phase

def create_network_ui(label: str, col) -> RLCNetwork:
    """Create UI elements for a network with unique keys"""
    with col:
        st.subheader(f"{label} Network")
        en_R = st.checkbox(f"Resistance {label[-1]}", value=True, key=f"r_checkbox_{label}")
        en_L = st.checkbox(f"Inductance {label[-1]}", key=f"l_checkbox_{label}")
        en_C = st.checkbox(f"Capacitance {label[-1]}", key=f"c_checkbox_{label}")
        wire = st.checkbox(f"Wire {label[-1]}", key=f"w_checkbox_{label}")
        
        R = st.slider(f"Resistance {label[-1]} (Ω)", 0.0, 1000.0, 100.0, step=10.0, 
                     key=f"r_slider_{label}") if en_R else None
        L = st.slider(f"Inductance {label[-1]} (mH)", 0.0, 1000.0, 100.0, step=1.0, 
                     key=f"l_slider_{label}") if en_L else None
        C = st.slider(f"Capacitance {label[-1]} (µF)", 0.0, 1000.0, 100.0, step=1.0, 
                     key=f"c_slider_{label}") if en_C else None
        
        return RLCNetwork(
            resistance=CircuitComponent(en_R, R),
            inductance=CircuitComponent(en_L, L),
            capacitance=CircuitComponent(en_C, C),
            wire=CircuitComponent(wire)
        )

def draw_circuit_diagram(network1: RLCNetwork, network2: RLCNetwork):
    """Draw circuit diagram with proper scaling"""
    with schemdraw.Drawing(figsize=(8, 4), dpi=150) as d:
        d.config(fontsize=11)
        
        # Source and ground
        d += elm.SourceSin().label('V_in')
        d += elm.Ground().at((0,0))
        d += elm.Line().right().at((0,3)).length(1)
        
        # Network 1 (Input)
        if network1.wire.enabled:
            d += elm.Line().right().at((1,3))
        if network1.resistance.enabled:
            d += elm.Resistor().right().label('R1').at((1,3))
        if network1.capacitance.enabled:
            d += elm.Capacitor().right().label('C1').at((1,4))
            d += elm.Line().down().at((1,4)).length(1)
            d += elm.Line().down().at((4,4)).length(1)
        if network1.inductance.enabled:
            d += elm.Inductor().right().label('L1').at((1,2))
            d += elm.Line().down().at((1,3)).length(1)
            d += elm.Line().down().at((4,3)).length(1)
            
        # Middle connection
        d += elm.Line().right().at((4,3)).length(2)
        d += elm.Line().down().at((5,3)).length(2)
        d += elm.Element().at((5, 1)).label("V_out", loc='bottom')
        
        # Network 2 (Output)
        if network2.wire.enabled:
            d += elm.Line().right().at((6,3))
        if network2.resistance.enabled:
            d += elm.Resistor().right().label('R2').at((6,3))
        if network2.capacitance.enabled:
            d += elm.Capacitor().right().label('C2').at((6,4))
            d += elm.Line().down().at((6,4)).length(1)
            d += elm.Line().down().at((9,4)).length(1)
        if network2.inductance.enabled:
            d += elm.Inductor().right().label('L2').at((6,2))
            d += elm.Line().down().at((6,3)).length(1)
            d += elm.Line().down().at((9,3)).length(1)
            
        # Final connections
        d += elm.Line().right().at((9,3)).length(1)
        d += elm.Line().down().at((10,3))
        d += elm.Ground().at((10,0))
        
        d.save('circuit.jpg')

def create_frequency_response_plot(frequencies, gain, phase, current_freq):
    """Create frequency response plot with proper sizing"""
    fig, (ax_gain, ax_phase) = plt.subplots(2, 1, figsize=(8, 6))
    fig.suptitle('Frequency Response', fontsize=14)
    
    # Magnitude plot
    ax_gain.semilogx(frequencies, gain, linewidth=1.5)
    ax_gain.set_xlabel('Frequency (Hz)', fontsize=10)
    ax_gain.set_ylabel('Magnitude (dB)', fontsize=10)
    ax_gain.grid(True, which="both", ls="-", alpha=0.6)
    ax_gain.axvline(current_freq, color='r', linestyle='--', alpha=0.5, 
                    label=f'Current: {current_freq:.1f} Hz')
    ax_gain.legend(fontsize=9)
    
    # Phase plot
    ax_phase.semilogx(frequencies, phase, linewidth=1.5)
    ax_phase.set_xlabel('Frequency (Hz)', fontsize=10)
    ax_phase.set_ylabel('Phase (degrees)', fontsize=10)
    ax_phase.grid(True, which="both", ls="-", alpha=0.6)
    ax_phase.axvline(current_freq, color='r', linestyle='--', alpha=0.5,
                     label=f'Current: {current_freq:.1f} Hz')
    ax_phase.legend(fontsize=9)
    
    plt.tight_layout()
    return fig

def create_oscilloscope_plot(t, input_signal, output_signal, input_amp, output_amp, time_window):
    """Create oscilloscope plot with proper sizing"""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6))
    fig.suptitle('Real-time Oscilloscope Display', fontsize=14)
    
    # Input waveform
    ax1.plot(t * 1000, input_signal, 'b-', label='Input', linewidth=1.5)
    ax1.set_ylabel('Voltage (V)', fontsize=10)
    ax1.set_title('Input Waveform', fontsize=12)
    ax1.set_xlim(0, time_window)
    ax1.set_ylim(-input_amp*1.2, input_amp*1.2)
    ax1.grid(True, alpha=0.6)
    ax1.legend(fontsize=9)
    
    # Output waveform
    ax2.plot(t * 1000, output_signal, 'r-', label='Output', linewidth=1.5)
    ax2.set_xlabel('Time (ms)', fontsize=10)
    ax2.set_ylabel('Voltage (V)', fontsize=10)
    ax2.set_title('Output Waveform', fontsize=12)
    ax2.set_xlim(0, time_window)
    ax2.set_ylim(-output_amp*1.2, output_amp*1.2)
    ax2.grid(True, alpha=0.6)
    ax2.legend(fontsize=9)
    
    plt.tight_layout()
    return fig

def main():
    st.set_page_config(
        page_title="RLC Network Simulator",
        page_icon="⚡",
        layout="centered",
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': 'mailto:ee23btech11217@iith.ac.in',
            'About': 'This is a lab exercise for analog circuits. For educational purposes only. Created by IITH ICDT students batch of 2023.'
        }
    )    

    st.title("Two-Port Parallel RLC Network Simulator")
    st.write("Interactive simulation of a two-port network with parallel RLC components")
    
    # Create two columns for network parameters
    col1, col2 = st.columns(2)
    network1 = create_network_ui("Input", col1)
    network2 = create_network_ui("Output", col2)
    
    # Draw circuit diagram
    draw_circuit_diagram(network1, network2)
    
    # Display circuit diagram with controlled width
    col1, col2, col3 = st.columns([1,4,1])
    with col2:
        st.image("circuit.jpg", caption="Two-Port RLC Network", use_container_width=True)

    # Signal parameters with improved ranges and defaults
    st.subheader("Signal Parameters")
    freq = st.slider("Frequency (Hz)", 0.1, 10000.0, 50.0, format="%.1f")
    amplitude = st.slider("Amplitude (V)", 0.1, 10.0, 5.0, format="%.1f")
    time_window = st.slider("Time Window (ms)", 1, 1000, 20)
    update_interval = st.slider("Update Interval (ms)", 10, 500, 50)
    
    # Frequency response with logarithmic scaling
    st.subheader("Frequency Response")
    freq_min = st.slider("Minimum Frequency (Hz)", 0.1, 100.0, 1.0, format="%.1f")
    freq_max = st.slider("Maximum Frequency (Hz)", 1000.0, 100000.0, 10000.0, format="%.1f")
    
    # Calculate and display frequency response
    frequencies, gain, phase = plot_frequency_response(network1, network2, [freq_min, freq_max])
    fig_freq = create_frequency_response_plot(frequencies, gain, phase, freq)
    st.pyplot(fig_freq)
    
    # Real-time oscilloscope
    if st.button("Start Oscilloscope", key="scope_button"):
        run_oscilloscope(network1, network2, freq, amplitude, time_window, update_interval)

def run_oscilloscope(network1, network2, freq, amplitude, time_window, update_interval):
    """Run real-time oscilloscope with improved visualization"""
    plot_placeholder = st.empty()
    start_time = time.time()
    
    try:
        while True:
            current_time = time.time() - start_time
            t = np.linspace(0, time_window/1000, 500)  # Increased resolution
            
            H = transfer_function(network1, network2, freq)
            output_amplitude = np.abs(H) * amplitude
            output_phase = np.angle(H)
            
            # Generate signals
            input_signal = amplitude * np.sin(2 * np.pi * freq * t - 2 * np.pi * freq * current_time)
            output_signal = output_amplitude * np.sin(2 * np.pi * freq * t - 2 * np.pi * freq * current_time + output_phase)
            
            # Create oscilloscope display
            fig = create_oscilloscope_plot(t, input_signal, output_signal, amplitude, output_amplitude, time_window)
            plot_placeholder.pyplot(fig)
            plt.close(fig)
            
            time.sleep(update_interval/1000)
    except Exception as e:
        st.error(f"Simulation error: {str(e)}")

if __name__ == "__main__":
    main()