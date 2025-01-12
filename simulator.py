import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import time

def calculate_parallel_impedance(R, L_mH, C_uF, omega):
    """Calculate complex impedance of RLC components in parallel"""
    L = L_mH / 1000
    C = C_uF / 1e6
    
    Z_R = R if R != 0 else float('inf')
    Z_L = 1j * omega * L if L != 0 else float('inf')
    Z_C = -1j / (omega * C) if C != 0 else float('inf')
    
    Z_total = 1 / (1/Z_R + 1/Z_L + 1/Z_C) if any([R != 0, L != 0, C != 0]) else float('inf')
    return Z_total

def transfer_function(R1, L1_mH, C1_uF, R2, L2_mH, C2_uF, freq):
    """Calculate transfer function of the two-port network with parallel RLCs"""
    omega = 2 * np.pi * freq
    Z1 = calculate_parallel_impedance(R1, L1_mH, C1_uF, omega)
    Z2 = calculate_parallel_impedance(R2, L2_mH, C2_uF, omega)
    return Z2 / (Z1 + Z2)

def generate_waveform(t, freq, amplitude, phase=0):
    """Generate sinusoidal waveform"""
    return amplitude * np.sin(2 * np.pi * freq * t + phase)

def plot_frequency_response(R1, L1_mH, C1_uF, R2, L2_mH, C2_uF, freq_range):
    """Generate frequency response plot"""
    frequencies = np.logspace(np.log10(freq_range[0]), np.log10(freq_range[1]), 1000)
    gain = []
    phase = []
    
    for f in frequencies:
        H = transfer_function(R1, L1_mH, C1_uF, R2, L2_mH, C2_uF, f)
        gain.append(20 * np.log10(np.abs(H)))
        phase.append(np.angle(H, deg=True))
    
    return frequencies, gain, phase

# Streamlit app
st.title("Two-Port RLC Network Analyzer")
st.image("two-port.png", caption="Two-Port Parallel RLC Network", use_container_width=True)

# Circuit parameters
col1, col2 = st.columns(2)
with col1:
    st.subheader("Input Network (Port 1)")
    R1 = st.slider("Resistance 1 (Ω)", 0.0, 1000.0, 100.0, step=10.0)
    L1 = st.slider("Inductance 1 (mH)", 0.0, 1000.0, 100.0, step=1.0)
    C1 = st.slider("Capacitance 1 (µF)", 0.0, 1000.0, 100.0, step=1.0)

with col2:
    st.subheader("Output Network (Port 2)")
    R2 = st.slider("Resistance 2 (Ω)", 0.0, 1000.0, 100.0, step=10.0)
    L2 = st.slider("Inductance 2 (mH)", 0.0, 1000.0, 100.0, step=1.0)
    C2 = st.slider("Capacitance 2 (µF)", 0.0, 1000.0, 100.0, step=1.0)

# Signal parameters
st.subheader("Signal Parameters")
freq = st.slider("Frequency (Hz)", 1, 1000, 50)
amplitude = st.slider("Amplitude (V)", 0.1, 10.0, 5.0)
time_window = st.slider("Time Window (ms)", 1, 100, 20)
update_interval = st.slider("Update Interval (ms)", 10, 100, 50)

# Frequency response parameters
st.subheader("Frequency Response Parameters")
freq_min = st.slider("Minimum Frequency (Hz)", 1, 100, 1)
freq_max = st.slider("Maximum Frequency (Hz)", 1000, 10000, 5000)

# Calculate transfer function and frequency response
H = transfer_function(R1, L1, C1, R2, L2, C2, freq)
output_amplitude = np.abs(H) * amplitude
output_phase = np.angle(H)

# Plot frequency response
frequencies, gain, phase = plot_frequency_response(R1, L1, C1, R2, L2, C2, [freq_min, freq_max])
fig_freq, (ax_gain, ax_phase) = plt.subplots(2, 1, figsize=(10, 8))
fig_freq.suptitle('Frequency Response')

# Magnitude plot
ax_gain.semilogx(frequencies, gain)
ax_gain.set_xlabel('Frequency (Hz)')
ax_gain.set_ylabel('Magnitude (dB)')
ax_gain.grid(True)
ax_gain.axvline(freq, color='r', linestyle='--', alpha=0.5, label=f'Current freq: {freq} Hz')
ax_gain.legend()

# Phase plot
ax_phase.semilogx(frequencies, phase)
ax_phase.set_xlabel('Frequency (Hz)')
ax_phase.set_ylabel('Phase (degrees)')
ax_phase.grid(True)
ax_phase.axvline(freq, color='r', linestyle='--', alpha=0.5, label=f'Current freq: {freq} Hz')
ax_phase.legend()

plt.tight_layout()
st.pyplot(fig_freq)

# Create a placeholder for the animated oscilloscope plot
plot_placeholder = st.empty()

# Animation loop
if st.button("Start Oscilloscope"):
    start_time = time.time()
    while True:
        # Current time
        current_time = time.time() - start_time
        
        # Create time vector for one complete window
        t = np.linspace(0, time_window/1000, 200)
        
        # Calculate phase offset based on current time
        phase_offset = 2 * np.pi * freq * current_time
        
        # Generate input and output signals
        input_signal = generate_waveform(t, freq, amplitude, -phase_offset)
        output_signal = generate_waveform(t, freq, output_amplitude, -phase_offset + output_phase)
        
        # Create the oscilloscope display
        fig_scope, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        fig_scope.suptitle('Real-time Oscilloscope Display')
        
        # Plot input waveform
        ax1.plot(t * 1000, input_signal, 'b-', label='Input', linewidth=2)
        ax1.set_ylabel('Voltage (V)')
        ax1.set_title('Input Waveform')
        ax1.set_xlim(0, time_window)
        ax1.set_ylim(-amplitude*1.2, amplitude*1.2)
        ax1.grid(True)
        ax1.legend()
        ax1.set_xticks([])
        
        # Plot output waveform
        ax2.plot(t * 1000, output_signal, 'r-', label='Output', linewidth=2)
        ax2.set_ylabel('Voltage (V)')
        ax2.set_title('Output Waveform')
        ax2.set_xlim(0, time_window)
        ax2.set_ylim(-output_amplitude*1.2, output_amplitude*1.2)
        ax2.grid(True)
        ax2.legend()
        ax2.set_xticks([])
        
        plt.tight_layout()
        
        # Update the oscilloscope plot
        plot_placeholder.pyplot(fig_scope)
        plt.close(fig_scope)
        
        # Wait for the specified update interval
        time.sleep(update_interval/1000)