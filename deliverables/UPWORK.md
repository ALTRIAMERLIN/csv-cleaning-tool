# Upwork portfolio text

Paste these into the Upwork portfolio form. Every number comes from this repository: the
recorded run (`demo/demo_manifest.json`) and the saved test run (`test-results/run_info.json`).
Do not add client names, results, time savings or other figures that are not in the repo.

## Project title

CSV Data Cleaning & Validation Tool (Python, Streamlit, CLI)

Characters: 60 (Upwork limit used here: 70)

## Project description

Personal demo project with synthetic data, not client work. A Python tool that cleans and validates a CSV file from a Streamlit web page or the command line; both use the same core code. It trims stray spaces, checks required fields and basic email format, and removes duplicates by chosen columns. No row is dropped silently: rejected rows go to issues.csv with their reason, every trimmed cell is logged, and summary.json reconciles the counts. The input file is never changed, and the same input and rules give identical output files. Includes 42 automated tests and a recorded end-to-end run.

Characters: 596, counted with spaces (limit for this project: 600)

## Your role

Developer (personal project)

## Skills

Python · Streamlit · Data Cleaning · Data Validation · CSV · pytest · Automation

## Content, in this order

| # | File | Note |
|---|---|---|
| 1 | `deliverables/cover.png` | Thumbnail, 2000x1500 (4:3; Upwork recommends 1000x750 or larger) |
| 2 | `video/out/csv-cleaning-tool-demo.mp4` | 55 s, 1920x1080, 8.0 MB, no audio, English captions |
| 3 | `deliverables/screenshot-1-rules.png` | Rules chosen from the file's own columns |
| 4 | `deliverables/screenshot-2-results-and-issues.png` | Counts, accounting check, issue rows with reasons |
| 5 | `deliverables/screenshot-3-summary-and-downloads.png` | summary.json and the four downloads with SHA-256 |
| 6 | Link | [github.com/ALTRIAMERLIN/csv-cleaning-tool](https://github.com/ALTRIAMERLIN/csv-cleaning-tool) |

If the form does not take video files, upload the MP4 to a video site (for example as an
unlisted video) and add the link instead. This was not checked on Upwork.
