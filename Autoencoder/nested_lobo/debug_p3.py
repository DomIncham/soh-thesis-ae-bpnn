import pandas as pd
p3 = pd.read_csv(r"C:\Master Degree\Thesis\Autoencoder\nested_lobo\nested_lobo_results.csv")
print("cols:", list(p3.columns))
print("dtypes:", p3.dtypes.to_dict())
p = p3[(p3.tolerance == 1)]
print("tol1 rows:", len(p))
print(p.head(3).to_string())
seeds, folds = [42], [1]
ok = [(r["seed"], r["test_battery"]) for _, r in p.iterrows()
      if r["seed"] in seeds and r["test_battery"] in ["B0005"]]
print("matching:", ok)
