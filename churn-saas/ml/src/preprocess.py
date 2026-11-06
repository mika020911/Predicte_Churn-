import pandas as pd

#charge les donner , decoupe : train 70 , validation 15 , test 15 
from config import (
    DATE_COLUMN, FEATURE_COLUMNS, RAW_DATA_PATH, TARGET_COLUMN,
    TRAIN_RATIO, VAL_RATIO,
)

def load_data(path=RAW_DATA_PATH):
    df = pd.read_csv(path, parse_dates=[DATE_COLUMN])
    missing = [c for c in FEATURE_COLUMNS + [TARGET_COLUMN, DATE_COLUMN] if c not in df.columns]
    if missing:
        raise ValueError(f"Colonnes manquantes dans le CSV : {missing}")
    return df

def temporal_split(df):
    date_train_end = df[DATE_COLUMN].quantile(TRAIN_RATIO)
    date_val_end = df[DATE_COLUMN].quantile(TRAIN_RATIO + VAL_RATIO)


    train = df[df[DATE_COLUMN] <= date_train_end]
    val = df[(df[DATE_COLUMN] > date_train_end) & (df[DATE_COLUMN] <= date_val_end)]
    test = df[df[DATE_COLUMN] > date_val_end]
    return train, val, test

def get_xy(df):
    return df[FEATURE_COLUMNS], df[TARGET_COLUMN]

def load_splits():
    train, val, test = temporal_split(load_data())
    return {"train": get_xy(train), "val": get_xy(val), "test": get_xy(test)}

def main():
    df = load_data()
    parts = dict(zip(("train", "val", "test"), temporal_split(df)))
    print(f"{'jeu':<6}{'lignes':>8}{'part':>8}{'churn':>9}   période")
    for name, part in parts.items():
        print(
            f"{name:<6}{len(part):>8}{len(part) / len(df):>8.0%}{part[TARGET_COLUMN].mean():>9.1%}"
            f"   {part[DATE_COLUMN].min().date()} -> {part[DATE_COLUMN].max().date()}"
        )

    # Contrôle : aucune période ne doit chevaucher la suivante
    assert parts["train"][DATE_COLUMN].max() < parts["val"][DATE_COLUMN].min()
    assert parts["val"][DATE_COLUMN].max() < parts["test"][DATE_COLUMN].min()
    assert sum(len(p) for p in parts.values()) == len(df)
    print("OK : pas de chevauchement dans le temps, aucune ligne perdue")


if __name__ == "__main__":
    main()