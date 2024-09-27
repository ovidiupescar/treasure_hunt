import pandas as pd
import numpy as np
import random

def calculate_options(row):
    if not row['text']:
        options = [row['Raspuns Corect'].strip(), row['Optiune 1'].strip(), row['Optiune 2'].strip()]
        random.shuffle(options)
        options_text = f'["{options[0]}", "{options[1]}", "{options[2]}"]'
    else:
        options_text = None
    return options_text

df = pd.read_csv("Orientare Urbana Oradea.csv", )


df['text'] = df['Optiune 1'].isna()
df['options'] = df.apply(calculate_options, axis=1)

df.to_pickle('intrebari.pkl')