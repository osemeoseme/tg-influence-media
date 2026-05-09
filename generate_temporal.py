#!/usr/bin/env python3
"""Generate temporal (time-series) visualizations."""

from src.processors.temporal_visualizations import TemporalVisualizer

if __name__ == "__main__":
    visualizer = TemporalVisualizer()
    visualizer.generate_all_visualizations()
