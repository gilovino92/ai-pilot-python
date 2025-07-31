#!/bin/bash
python -m venv venv
source venv/bin/activate
uvicorn main:app --reload --port 8888