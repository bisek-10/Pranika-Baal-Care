import os

def create_folders():
    paths = [
        "static/css",
        "static/js",
        "static/images",
        "templates"
    ]
    for p in paths:
        os.makedirs(p, exist_ok=True)
        
create_folders()
