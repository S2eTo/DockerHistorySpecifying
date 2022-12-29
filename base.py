import os

BASE_DIR = os.path.dirname(__file__)
DATABASE_DIR = os.path.join(BASE_DIR, "databases")

if not os.path.exists(DATABASE_DIR):
    os.mkdir(DATABASE_DIR)

