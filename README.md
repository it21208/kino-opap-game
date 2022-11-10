# Earth Science Analytics - Backend coding challenge

The goal of this coding challenge is to enhance and extend a simple Python script that computes player payouts for the game of [KINO](https://www.opap.gr/en/how-to-play-kino).

KINO is a popular lottery-like gambling game offered by [OPAP](https://www.opap.gr). In short:

- Draws occur daily every 5 minutes from 9:00 to 23:55, i.e. there are 180 draws per day.
- In each draw 20 numbers are drawn at random from 1 through 80.
- A player chooses between 1 and 12 numbers ranging from 1 through 80.
- The player's rate of return (payout) is based on a [pay-table](https://www.opap.gr/en/kino-pay-table) that takes into account:
    - How many numbers were chosen.
    - The number of matches out of those chosen.

_Note: The [ODDS-EVEN](https://www.opap.gr/en/meet-odds-evens) and [COLUMNS](https://www.opap.gr/en/meet-columns) betting options are not part of this challenge._


## KINO payout calculator

In this repository you will find `kino.py`, a command line interface (CLI) for calculating the mean payout of a given set of chosen numbers across all (or a subset of) draws on a given date. The script fetches the winning numbers by making one or more HTTP requests to an [OPAP Web Service](https://www.opap.gr/web-services) URL and extracting the relevant property of the JSON response.

Usage:

	$ python kino.py --help
	usage: kino.py [-h] [-d DATE] [-p PAGE [PAGE ...]] [--debug]
	               NUMBER [NUMBER ...]

	KINO payout calculator

	positional arguments:
	  NUMBER                One or more selected numbers, up to 12

	optional arguments:
	  -h, --help            show this help message and exit
	  -d DATE, --date DATE  Draw date in YYYY-MM-DD format (default: 2020-07-19)
	  -p PAGE [PAGE ...], --page PAGE [PAGE ...]
	                        Fetch only the given page(s) of draws for the given
	                        date (default: None)
	  --debug               Log each draw for debugging (default: False)

Sample run:

	$ python kino.py --date=2020-06-25 5 12 19 39 62 74 78
	{"selected_numbers": [5, 12, 19, 39, 62, 74, 78], "date": "2020-06-25", "pages": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18], "num_payouts": 180, "mean_payout": 0.5333333333333333}

Sample run limited to the first 2 pages (=20 draws) of the same date:

	$ python kino.py --page 1 2 --date=2020-06-25 5 12 19 39 62 74 78
	{"selected_numbers": [5, 12, 19, 39, 62, 74, 78], "date": "2020-06-25", "pages": [1, 2], "num_payouts": 20, "mean_payout": 0.45}


## Tasks

### 1. Refactoring

Currently `kino.py` is written as a monolithic script: it parses the command line arguments, fetches the winning numbers, computes the payouts and prints the results, all in global scope.

Refactor it so that it becomes easier to test, extend and maintain.

### 2a. KINO Bonus

Extend the payout calculator with the [KINO BONUS](https://www.opap.gr/en/meet-kino-bonus) option:

- Add an optional `-b`/`--bonus` CLI flag.
- Implement the payout calculation logic for KINO BONUS that is applied if `--bonus` is given.

Sample run:

	$ python kino.py --bonus --date=2020-06-25 5 12 19 39 62 74 78
	{"selected_numbers": [5, 12, 19, 39, 62, 74, 78], "bonus": true, "date": "2020-06-25", "pages": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18], "num_payouts": 180, "mean_payout": 0.8333333333333334}

Sample run limited to the first 2 pages (=20 draws) of the same date:

	$ python kino.py --bonus --page 1 2 --date=2020-06-25 5 12 19 39 62 74 78
	{"selected_numbers": [5, 12, 19, 39, 62, 74, 78], "bonus": true, "date": "2020-06-25", "pages": [1, 2], "num_payouts": 20, "mean_payout": 0.6}


### 2b. Caching

Implement a caching mechanism that can be used for saving and loading the winning numbers from the local disk instead of the network.

- Add an optional `-c/--cache DIR` CLI option that accepts a directory path as input.
- The first time the script runs for a given date and page(s), the fetched winning numbers are saved under `DIR`.
- Any subsequent runs for the same date and page(s) load the winning numbers from `DIR`.

What file(s) are written under `DIR`, in what format and any other implementation details are left up to you.

_Tip: You may find [joblib.Memory](https://joblib.readthedocs.io/en/latest/memory.html) convenient for this task._

### 2c. Optimization

The payout computation is executed sequentially, one draw at a time. Try to reduce the overall computation time by:

- either parallelization using [multiprocessing](https://docs.python.org/3/library/multiprocessing.html),
- or [vectorized operations](https://realpython.com/numpy-array-programming/) using [NumPy](https://numpy.org/) (or/and [Pandas](https://pandas.pydata.org/)).

## Submission Guidelines

- Create a separate git branch for each task you work on and open separate pull request(s).
- Your code should run on Python >= 3.6.
- You may use any external Python packages as dependencies; just make sure you add them to `requirements.txt`.
- Use [black](https://github.com/psf/black) to format your code.
