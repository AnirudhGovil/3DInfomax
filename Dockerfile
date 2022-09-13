# Define base image
FROM continuumio/miniconda3
 
# Set working directory for the project
WORKDIR /3DINFOMAX

COPY . .
 
# Create Conda environment from the YAML file
RUN conda env create -f environment1.yml
 
# Override default shell and use bash
SHELL ["conda", "run", "-n", "3DINFOMAX", "/bin/bash", "-c"]
 
# Python program to run in the container
ENTRYPOINT ["conda", "run", "-n", "3DINFOMAX", "python", "test.py"]