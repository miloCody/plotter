import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO

# --- App state: Measurements ---
if "measurements" not in st.session_state:
    st.session_state.measurements = [(0.0, 0.0)]  # start with one row

# --- UI Layout ---
st.title("Intersection Plotter")
section_name = st.text_input("Section / Square:", value="Section 8 Square 42")

st.subheader("Measurements (West / East in cm)")

# Dynamic measurement rows
for i, (west, east) in enumerate(st.session_state.measurements):
    cols = st.columns([1, 1, 1, 1])
    with cols[0]:
        st.write(f"F{i+1}:")
    with cols[1]:
        st.session_state.measurements[i] = (st.number_input(f"West {i+1}", value=west, key=f"west{i}"),
                                            st.session_state.measurements[i][1])
    with cols[2]:
        st.session_state.measurements[i] = (st.session_state.measurements[i][0],
                                            st.number_input(f"East {i+1}", value=east, key=f"east{i}"))
    with cols[3]:
        if st.button("Delete", key=f"del{i}"):
            st.session_state.measurements.pop(i)
            st.experimental_rerun()  # refresh to update indices

if st.button("Add Measurement"):
    st.session_state.measurements.append((0.0, 0.0))
    st.experimental_rerun()

# --- Plot Intersections ---
def calculate_intersections(measurements, d=350):
    valid_points = []
    invalid_pairs = []

    for i, (west_distance, east_distance) in enumerate(measurements, start=1):
        label = f"F{i}"

        if d > west_distance + east_distance:
            invalid_pairs.append((label, west_distance, east_distance, "too far apart"))
            continue
        if d < abs(west_distance - east_distance):
            invalid_pairs.append((label, west_distance, east_distance, "one circle inside another"))
            continue

        a = (west_distance ** 2 - east_distance ** 2 + d ** 2) / (2 * d)
        h_sq = west_distance ** 2 - a ** 2
        if h_sq < 0:
            invalid_pairs.append((label, west_distance, east_distance, "no real intersection"))
            continue

        h = np.sqrt(h_sq)
        x_intersect = a
        y_intersect = h
        valid_points.append((label, x_intersect, y_intersect))

    return valid_points, invalid_pairs

def plot_grid(valid_points, section_name):
    side_length = 350
    grid_spacing = 10
    tick_interval = 50

    fig, ax = plt.subplots(figsize=(6,6), dpi=100)
    ax.set_xlim(0, side_length)
    ax.set_ylim(0, side_length)
    ax.set_aspect('equal', adjustable='box')

    # Grid lines
    lines = np.arange(0, side_length + grid_spacing, grid_spacing)
    for x in lines:
        ax.plot([x,x],[0,side_length], color='gray', linewidth=0.8)
    for y in lines:
        ax.plot([0,side_length],[y,y], color='gray', linewidth=0.8)

    # Ticks
    ticks = np.arange(0, side_length + tick_interval, tick_interval)
    ax.set_xticks(ticks)
    ax.set_yticks(ticks)
    ax.set_xticklabels([str(int(t)) for t in ticks])
    ax.set_yticklabels([str(int(t)) for t in ticks])

    # Labels
    ax.set_xlabel(section_name)
    ax.set_ylabel("Scale: 1 square = 10cm")
    ax.set_title("North ↑")

    for label, x, y in valid_points:
        ax.plot(x, y, 'go', markersize=6)
        offset_x = 8 if int(label[1:]) % 2 == 0 else -12
        offset_y = 8 if int(label[1:]) % 3 == 0 else -10
        ax.text(x + offset_x, y + offset_y, label,
                color='black', fontsize=8, fontweight='bold',
                bbox=dict(facecolor='white', edgecolor='none', alpha=0.6, pad=0.5))

    return fig

if st.button("Plot Intersections"):
    valid_points, invalid_pairs = calculate_intersections(st.session_state.measurements)

    st.subheader("Results")
    if valid_points:
        st.write("**Intersecting Points Found:**")
        for label, x, y in valid_points:
            st.write(f"{label}: x = {x:.1f} cm, y = {y:.1f} cm")
    else:
        st.write("No valid intersections found.")

    if invalid_pairs:
        st.write("**Non-intersecting Pairs:**")
        for label, w, e, reason in invalid_pairs:
            st.write(f"{label}: west={w}, east={e} --> {reason}")

    fig = plot_grid(valid_points, section_name)
    st.pyplot(fig)

    # Save plot as PNG
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=300)
    st.download_button("Download Plot as PNG", data=buf.getvalue(), file_name="intersection_plot.png", mime="image/png")
