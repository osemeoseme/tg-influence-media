#!/usr/bin/env python3
"""Generate extended insight visualizations."""

from src.processors.extended_visualizations import ExtendedVisualizer

if __name__ == "__main__":
    visualizer = ExtendedVisualizer()
    visualizer.generate_all_visualizations()
