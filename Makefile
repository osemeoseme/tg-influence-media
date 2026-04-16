# Makefile for Media Influence Analysis Project

.PHONY: help setup install scrape analyze report all clean

help:
	@echo "Available commands:"
	@echo "  make setup      - Set up the project (create venv, install dependencies)"
	@echo "  make scrape     - Scrape data from Telegram and media sources"
	@echo "  make analyze    - Analyze the scraped data"
	@echo "  make report     - Generate reports and visualizations"
	@echo "  make all        - Run complete pipeline (scrape + analyze + report)"
	@echo "  make explore    - Run exploratory analysis"
	@echo "  make clean      - Clean data and results"
	@echo "  make clean-all  - Clean everything including venv"

setup:
	@echo "Setting up project..."
	@bash setup.sh

install:
	@echo "Installing dependencies..."
	@pip install -r requirements.txt

scrape:
	@echo "Scraping data..."
	@python main.py scrape

analyze:
	@echo "Analyzing data..."
	@python main.py analyze

report:
	@echo "Generating reports..."
	@python main.py report

all:
	@echo "Running complete pipeline..."
	@python main.py all

explore:
	@echo "Running exploratory analysis..."
	@python notebooks/exploratory_analysis.py

clean:
	@echo "Cleaning data and results..."
	@rm -rf data/raw/*
	@rm -rf data/processed/*
	@rm -rf data/results/*
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.session" -delete 2>/dev/null || true
	@find . -type f -name "*.session-journal" -delete 2>/dev/null || true
	@echo "Clean complete."

clean-all: clean
	@echo "Removing virtual environment..."
	@rm -rf venv
	@echo "Clean all complete."
