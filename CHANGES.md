
## Changelog **x4i3_tools**

### 0.2.0 26/05/2021

- Partially removed Python 2.7 compatibility
- Split the spaghetti file into new package x4i3tools
- thematically ordered modules
- support for the "new" format X4-2021-...
- debugged for using x4i3 package and the 2021 EXFOR datasets
- multi-processing for parsing and transaction based mysql3 fill -> 1000 times faster building of new databases

### 0.1.0 17/01/2020

- initial release of the support tools for the fork x4i3 formerly part of `x4i`
- compatibility with Python 2 and 3
- setup_exfor_db.py capsuled and not messing with the files of the x4i3 package anymore
- Removed most of the "NonImplmented" stuff
- Windows compatible
- autopep8-ed (but didn't really help)
- added -f force flag to trigger overwriting of current directories
