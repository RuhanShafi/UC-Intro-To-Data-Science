"""Dashboard data: recompute every figure from the personalised data files.

Run from the folder that contains the data/ directory created by
the setup chunk of the Rmd.
"""
import numpy as np
import pandas as pd

D = "data/"
emis = pd.read_csv(D + "Emissions.csv").drop_duplicates()
renw = pd.read_csv(D + "Renewables.csv")
ctry = pd.read_csv(D + "Countries.csv")


def interp(s):
    return s.interpolate(limit_direction="both")


emis = emis.sort_values(["iso_code", "year"])
emis.loc[emis.annual_co2_mt < 0, "annual_co2_mt"] = np.nan
emis.loc[emis.annual_oil_co2_mt == -999, "annual_oil_co2_mt"] = np.nan
emis["annual_co2_mt"] = emis.groupby("iso_code").annual_co2_mt.transform(interp)

annual = emis.groupby("year").annual_co2_mt.sum()

# Renewables: drop aggregates, interpolate blanks within each country.
renw = renw[~renw["Country.Region"].isin(["World", "European Union (27)"])]
long = renw.melt("Country.Region", var_name="year", value_name="twh")
long["year"] = long.year.astype(int)
long = long.sort_values(["Country.Region", "year"])
long["twh"] = long.groupby("Country.Region").twh.transform(interp)
annual_renew = long.groupby("year").twh.sum()

# Cumulative CO2 per person in the final year (Chile population fixed).
chile = ctry.Country == "Chile"
ctry.loc[chile, "popData2022"] = round(448338e6 / 22929)
cum = emis.groupby("iso_code").annual_co2_mt.sum().rename("cum")
pc = ctry.set_index("countryCode").join(cum)
pc["co2_pc"] = pc.cum * 1e6 / pc.popData2022

# Small multiples: annual CO2 and renewables indexed to 2004 = 100.
renw_names = {"DEU": "Germany", "USA": "United States of America",
              "CHN": "China", "IND": "India"}
multiples = {}
for iso, rname in renw_names.items():
    co2 = emis[emis.iso_code == iso].set_index("year").annual_co2_mt
    rn = long[long["Country.Region"] == rname].set_index("year").twh
    multiples[iso] = (100 * co2 / co2.iloc[0], 100 * rn / rn.iloc[0])

if __name__ == "__main__":
    print("2023 total:", round(annual.loc[2023], 1))
    print("2020 change:", round(annual.loc[2020] - annual.loc[2019], 1))
    print("Renewables 2004 / 2023:", round(annual_renew.loc[2004], 1),
          round(annual_renew.loc[2023], 1))
    print(pc.sort_values("co2_pc", ascending=False)
          [["Country", "co2_pc", "cum"]].head(6).round(1))
    print(pc.loc[["CHN", "USA", "IND", "RUS", "JPN"], ["cum"]].round(1))
