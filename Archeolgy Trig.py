import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO

# --- Page setup ---
st.set_page_config(page_title="Intersection Plotter", layout="wide")

# --- Session state for measurements ---
if 'measurements' not in st.session_state:
    st.session_state.measurements = [["", ""]]  # Start with 1 row

if 'plot_fig' not in st.session_state:
    st.session_state.plot_fig = None  # Store last figure

# --- Section/Square name ---
section_name = st.text_input("Section / Square", value="Section 8 Square 42")

# --- Display measurement rows ---
st.write("### Measurements (West / East in cm)")
for i, measurement in enumerate(st.session_state.measurements):
    row_cols = st.columns([3, 3, 1])
    measurement[0] = row_cols[0].text_input(f"West F{i+1}", value=measurement[0], key=f"west_{i}")
    measurement[1] = row_cols[1].text_input(f"East F{i+1}", value=measurement[1], key=f"east_{i}")
    if row_cols[2].button("Delete", key=f"del_{i}"):
        st.session_state.measurements.pop(i)
        st.experimental_rerun()

# --- Add / Clear buttons below measurements ---
btn_cols = st.columns([1,1])
if btn_cols[0].button("Add Measurement"):
    st.session_state.measurements.append(["", ""])
    st.experimental_rerun()

if btn_cols[1].button("Clear Plot & Measurements"):
    st.session_state.measurements = [["", ""]]
    st.session_state.plot_fig = None
    st.experimental_rerun()

# --- Plot button ---
plot_clicked = st.button("Plot Intersections")

# --- Output and plot areas ---
results_area = st.empty()
plot_area = st.empty()

if plot_clicked:
    # --- Grid parameters ---
    side_length = 350
    grid_spacing = 10
    tick_interval = 50

    east_pivot_x = 350
    west_pivot_x = 0
    d = east_pivot_x - west_pivot_x

    valid_points = []
    invalid_pairs = []

    # --- Create figure ---
    fig, ax = plt.subplots(figsize=(6, 6), dpi=100)
    ax.set_xlim(0, side_length)
    ax.set_ylim(0, side_length)
    ax.set_aspect('equal', adjustable='box')

    # Grid lines
    lines = np.arange(0, side_length + grid_spacing, grid_spacing)
    for x in lines:
        ax.plot([x, x], [0, side_length], color='gray', linewidth=0.8)
    for y in lines:
        ax.plot([0, side_length], [y, y], color='gray', linewidth=0.8)

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
    for spine in ax.spines.values():
        spine.set_linewidth(2)

    # --- Process measurements ---
    for i, (west_val, east_val) in enumerate(st.session_state.measurements):
        label = f"F{i+1}"
        try:
            west_distance = float(west_val)
            east_distance = float(east_val)
        except ValueError:
            continue

        # Validation
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
        ax.plot(x_intersect, y_intersect, 'go', markersize=6)

        # Label offsets
        offset_x = 8 if i % 2 == 0 else -12
        offset_y = 8 if i % 3 == 0 else -10
        ax.text(x_intersect + offset_x, y_intersect + offset_y, label,
                color='black', fontsize=8, fontweight='bold',
                bbox=dict(facecolor='white', edgecolor='none', alpha=0.6, pad=0.5))

    # --- Display results ---
    result_text = ""
    if valid_points:
        result_text += "Intersecting Points Found:\n"
        for label, x, y in valid_points:
            result_text += f"  {label}: x = {x:.1f} cm, y = {y:.1f} cm\n"
    else:
        result_text += "No valid intersections found.\n"

    if invalid_pairs:
        result_text += "\nNon-intersecting Pairs:\n"
        for label, w, e, reason in invalid_pairs:
            result_text += f"  {label}: west={w}, east={e} --> {reason}\n"

    results_area.text_area("Results", value=result_text, height=300)

    # --- Show plot ---
    st.session_state.plot_fig = fig
    plot_area.pyplot(fig)

# --- Save plot as PNG ---
if st.session_state.plot_fig is not None:
    buffer = BytesIO()
    st.session_state.plot_fig.savefig(buffer, format="png")
    buffer.seek(0)
    st.download_button(
        label="Save Plot as PNG",
        data=buffer,
        file_name="intersection_plot.png",
        mime="image/png"
    )
