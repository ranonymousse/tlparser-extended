> *This artifact extends the open-source `tlparser`[^tlparser] to automatically analyze requirements expressed in natural language and support their quality evaluation.*
> *The codebase was obtained by forking original `tlparser` repository and augmenting it with these features.*

- Direct link to Edge/IoT dataset: [**Dataset.xlsx**](./data/Edge_IoT/Dataset.xlsx)

</br>

# Temporal Logic Parser (Extended)

The Temporal Logic Parser or `tlparser` takes something like this as input:

```
G((y and u == 9) --> F(not y or i < 3))
```

And returns some statistics about it:

```json
{
  "agg": {
    "aps": 3,
    "cops": 2,
    "lops": 4,
    "tops": 2
  },
  "ap": [
    "i_lt_3",
    "u_eq_9",
    "y"
  ],
  "asth": 5,
  "cops": {
    "eq": 1,
    "geq": 0,
    "gt": 0,
    "leq": 0,
    "lt": 1,
    "neq": 0
  },
  "entropy": {
    "lops": 1,
    "lops_tops": 2.585,
    "tops": 2
  },
  "lops": {
    "and": 1,
    "impl": 1,
    "not": 1,
    "or": 1
  },
  "tops": {
    "A": 0,
    "E": 0,
    "F": 1,
    "G": 1,
    "R": 0,
    "U": 0,
    "X": 0
  }
}
```

## How to use

First, `git clone` this repository and `cd` into the folder.
Listing the contents of this directory (e.g., using `ls -la` on Unix or `dir /a` on Windows) should return the following items:

```bash
.
├── .git              (folder)
├── .github           (folder)
├── .gitignore
├── .vscode           (folder)
├── LICENSE
├── README.md
├── data              (folder)
├── pyproject.toml
├── pytest.ini
├── tests             (folder)
└── tlparser          (folder)
```

> [!NOTE]  
> This tool requires **Python 3.10 or later**. Ensure you have the correct version [installed](https://www.python.org/downloads/).

Next, create a new virtual environment using the following commands:

```bash
# macOS/Linux
python3 -m venv venv && source venv/bin/activate

# Windows
# py -3 -m venv venv && venv\Scripts\activat
```

Install and test the dependencies:

```bash
pip3 install --upgrade pip && pip3 install -e '.[test]' && python3 -m pytest
```

Now you are ready to start the `tlparser`.
Test it by printing the `help` message.

```bash
tlparser --help
```

<details>
<summary>Process and plot test data (optional)</summary>

First, digest the test data file to create an Excel file.

```bash
tlparser digest ./tests/data/test.json
```

The Excel file will serve as basis for generating the plots.
To generate all plots of the latest Excel file execute the following command:

```bash
tlparser visualize -l -p all
# plots are written to ./tlparser/workingdir/
```

All plots are saved to `./tlparser/workingdir/`.

</details>

You can parse the `spacewire` requirements using the following command:

```bash
tlparser digest ./data/spacewire.json
```

The resulting Excel file serves as basis for generating the plots.
It contains the following columns:

| Column                 | Meaning                                                                                                                                               |
|------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------|
| id                     | Unique requirement identifier                                                                                                                         |
| text                   | Requirement in human language                                                                                                                         |
| type                   | Temporal logic (supported are `INV`, `LTL`, `MTLb`, `MITL`, `TPTL`, `CTLS`, `STL`)                                                                    |
| reasoning              | Thought decisive for formalizing the requirement in this logic                                                                                        |
| translation                | Specified whether the requirement can theoretically be formalized in (*translated to*) another logic (possible values are `self`, `yes`, `no`, `unknown`) |
| translation class              | Category name derived by concatenating first letters of all translation cases per requirement                                                           |
| stats.formula_raw      | Formalization with comparison operators (e.g. `G((x <= 7) --> (not (y)))`)                                                                            |
| stats.formula_parsable | Formalization without comparison operators (e.g. `G((x_leq_7) --> (not (y)))`)                                                                        |
| stats.formula_parsed   | Interpreted formalization using [`pyModelChecking`](https://github.com/albertocasagrande/pyModelChecking) (e.g. `G((x_leq_7 --> not y))`)             |
| stats.asth             | Height (or *depth* or *nesting*) of the abstract syntax tree                                                                                          |
| stats.ap               | Set of all atomic propositions                                                                                                                        |
| stats.cops.eq          | Number of `==` (equals) comparisons                                                                                                                   |
| stats.cops.ge          | Number of `>=` (greater-or-equal-than) comparisons                                                                                                    |
| stats.cops.gt          | Number of `>` (greater-than) comparisons                                                                                                              |
| stats.cops.leq         | Number of `<=`less-or-equal-than comparisons                                                                                                          |
| stats.cops.lt          | Number of `<` (less-than) comparisons                                                                                                                 |
| stats.cops.ne          | Number of `!=` (not-equals) comparisons                                                                                                               |
| stats.lops.and         | Number of `∧` (and) operators                                                                                                                         |
| stats.lops.imp         | Number of `-->` (implies) operators                                                                                                                   |
| stats.lops.not         | Number of `¬` (not) operators                                                                                                                         |
| stats.lops.or          | Number of `∨` (or) operators                                                                                                                          |
| stats.tops.A           | Number of `for all paths` operators                                                                                                                   |
| stats.tops.E           | Number of `there exists a path` operators                                                                                                             |
| stats.tops.F           | Number of `eventually` (diamond symbol) operators                                                                                                     |
| stats.tops.G           | Number of `globally` (square symbol) operators                                                                                                        |
| stats.tops.R           | Number of `release` operators                                                                                                                         |
| stats.tops.U           | Number of `until` operators                                                                                                                           |
| stats.tops.X           | Number of `next` operators                                                                                                                            |
| stats.agg.aps          | Total number of atomic propositions                                                                                                                   |
| stats.agg.cops         | Total number of comparison operators (`==`, `!=`, `<`, `>`, `=>`, `<=`)                                                                               |
| stats.agg.lops         | Total number of logical operators (`∧`, `∨`, `-->`, `¬`)                                                                                              |
| stats.agg.tops         | Total number of temporal operators (`A`, `E`, `F`, `G`, `R`, `U`, `X`)                                                                                |

To generate all plots of the latest Excel file execute the following command:

```bash
tlparser visualize -l -p all
```

All plots are saved to `./tlparser/workingdir/`.

To clean-up all generated files again, execute the following command and confirm with `y`:

```bash
tlparser cleanup
```

Exit the virtual environment again using this command:

```bash
deactivate
```

To activate it again, simply execute this command in the root folder of the repository:

```bash
# from repo root
source venv/bin/activate

# or on Windows:
# venv\Scripts\activate
```

</br>

[^tlparser]: Bögli, R., Rohani, A., Studer, T., Tsigkanos, C., & Kehrer, T. tlparser [Computer software]. <https://github.com/SEG-UNIBE/tlparser>
