import argparse
import itertools as it
import json
import sys
from argparse import ArgumentParser, Namespace
from collections import namedtuple
from datetime import datetime
from joblib import Memory
import multiprocessing as mp

import requests

from constants import PAYOUT_TABLE


def parse_arguments() -> ArgumentParser:
    """
    This method is responsible for parsing arguments passed to the script.

    There are presently five possible arguments, namely:
    NUMBER: One or more selected numbers, up to 12.
    HELP: show the help message and exit
    DATE: Draw date in YYYY-MM-DD format (default is 2020-07-19)
    PAGE: Fetch only the given page(s) of draws for the given date (default is None).
    DEBUG: Log each draw for debugging (default is False)


    Attributes
    ----------


    Returns
    -------
    parser
        The ArgumentParser object.
    """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="KINO payout calculator",
    )
    parser.add_argument(
        "numbers",
        nargs="+",
        type=int,
        choices=range(1, 81),
        metavar="NUMBER",
        help="One or more selected numbers, up to 12",
    )
    parser.add_argument(
        "-b",
        "--bonus",
        action="store_true",
        help="Play with KINO bonus",
    )
    parser.add_argument(
        "-d",
        "--date",
        default=str(datetime.today().date()),
        help="Draw date in YYYY-MM-DD format",
    )
    parser.add_argument(
        "-p",
        "--page",
        type=int,
        choices=range(1, 19),
        nargs="+",
        metavar="PAGE",
        help="Fetch only the given page(s) of draws for the given date",
    )
    parser.add_argument(
        "-c",
        "--cache",
        type=str,
        nargs="+",
        metavar="CACHE",
        help="Caching of results",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Log each draw for debugging",
    )
    return parser


def validate_parse_args(
    opts: Namespace, count_numbers_selected: int, parser: ArgumentParser
) -> None:
    """
    The current method is responsible for validating the length and uniqueness of the numbers inserted and date validation.


    Attributes
    ----------
    opts : argparse.Namespace
        The argparse.Namespace object.
    count_numbers_selected : int
        The number of selected numbers by the kino player.
    parser : argparse.ArgumentParser
        The argparse.ArgumentParser object


    Returns
    ----------
    None
    """
    if count_numbers_selected > 12:
        parser.error("Up to 12 numbers can be selected")
    if count_numbers_selected != len(set(opts.numbers)):
        parser.error("Selected numbers can not contain duplicates")

    try:
        opts.date = datetime.strptime(opts.date, "%Y-%m-%d").date()
    except ValueError as ex:
        parser.error(ex)


def handle_pages_logic(opts: Namespace, Draw: type):
    """
    The current method implements the pages logic. A different logic is implemented if pages numbers are given by the user and an alternative implementation if pages are not specified by the user.


    Attributes
    ----------
    opts : argparse.Namespace
        The argparse.Namespace object.
    Draw : type
        A named tuple called Draw with fields of id and numbers.


    Returns
    ----------
    draws_pages_tuple : tuple
        A tuple with all (or a subset of) draws returned and the pages.
    -------
    """
    draws = []
    pages = opts.page or []
    # The OPAP Web Service URL.
    url = f"https://api.opap.gr/draws/v3.0/1100/draw-date/{opts.date}/{opts.date}"
    session = requests.Session()
    if pages:
        for page in pages:
            try:
                resp = session.get(url, params={"page": page - 1}).json()
            except requests.ConnectionError as e:
                print(str(e))
                sys.exit("Exiting because of ConnectionError..")
            except requests.Timeout as e:
                print(str(e))
                sys.exit("Exiting because of Timeout..")
            except requests.RequestException as e:
                print(str(e))
                sys.exit("Exiting because of RequestException..")
            for draw in resp["content"]:
                draws.append(Draw(draw["drawId"], draw["winningNumbers"]["list"]))
    else:  # fetch all pages
        for page in it.count(start=1):
            try:
                resp = session.get(url, params={"page": page - 1}).json()
            except requests.ConnectionError as e:
                print(str(e))
                sys.exit("Exiting because of ConnectionError..")
            except requests.Timeout as e:
                print(str(e))
                sys.exit("Exiting because of Timeout..")
            except requests.RequestException as e:
                print(str(e))
                sys.exit("Exiting because of RequestException..")
            if resp["content"]:
                pages.append(page)
                for draw in resp["content"]:
                    draws.append(
                        Draw(draw["drawId"], draw["winningNumbers"]["list"])
                    )
            if resp["last"]:
                break
    
    draws_pages_tuple = (draws, pages)
    return draws_pages_tuple


def task(opts, payout):
    """ 
    A simple task to parallelize with multiprocessing.
    """
    if opts.bonus:
        return payout*2
    else:   
        return payout


def payout_computation(draw, selected, selected_payouts, opts):
    """ 
    The method that is responsible for implementing the payout computation for each draw.
    
    Attributes
    ----------
    draw : __main__.Draw
    selected : frozenset
    selected_payouts : dict
        The selected payouts.
    opts : argparse.Namespace
        The argparse.Namespace.
    """
    matches = selected.intersection(draw.numbers)
    payout = selected_payouts.get(len(matches), 0)
    if opts.debug:
        print(f"{draw}: matches={sorted(matches)}, payout={payout}", file=sys.stderr)
    return task(opts, payout)
    

def get_payouts(opts: Namespace, draws: list) -> list:
    """
    A method to get the payouts for the provided draws.

    Attributes
    ----------
    opts : argparse.Namespace
        The argparse.Namespace object.
    draws : list
        The draws for the given date.


    Returns
    ----------
    payouts : list
        A list holding the payouts.
    """
    selected = frozenset(opts.numbers)
    selected_payouts = PAYOUT_TABLE[len(selected)]
    payouts = []
    pool = mp.Pool(mp.cpu_count())
    payouts = [pool.apply(payout_computation, args=(draw, selected, selected_payouts, opts)) for draw in draws]
    pool.close()
    return payouts


def main(Draw) -> str:
    """
    The main method implements the core logic of the computation of player payouts for the game of KINO a popular lottery-like gambling game offered by OPAP.


    Attributes
    ----------
    Draw : type
        A named tuple called Draw with fields of id and numbers.

    Returns
    results : str
        The payout results.
    -------
    """
    # The command below returns a new subclass of tuple with named fields.
    parser = parse_arguments()
    opts = parser.parse_args()
    count_numbers_selected = len(opts.numbers)

    # Basic validation of two input arguments
    validate_parse_args(opts, count_numbers_selected, parser)
    
    # Check if caching option has been choosen
    if opts.cache is not None:
        import os
        cachedir = os.path.join(os.getcwd(), opts.cache[0])
        memory = Memory(cachedir, verbose=0)
        handle_pages_logic_cached = memory.cache(handle_pages_logic)
        draws, pages = handle_pages_logic_cached(opts, Draw)
    else:
        # Get all (or a subset of) draws returned and the pages
        draws, pages = handle_pages_logic(opts, Draw)

    # Get payouts    
    payouts = get_payouts(opts, draws)
    

    if opts.bonus:
        result = {
            "selected_numbers": opts.numbers,
            "bonus": opts.bonus,
            "date": str(opts.date),
            "pages": pages,
            "num_payouts": len(payouts),
            "mean_payout": sum(payouts) / +len(payouts) if payouts else None,
        }
    else:    
        result = {
            "selected_numbers": opts.numbers,
            "date": str(opts.date),
            "pages": pages,
            "num_payouts": len(payouts),
            "mean_payout": sum(payouts) / len(payouts) if payouts else None,
        }

    results = json.dumps(result)
    return results


if __name__ == "__main__":
    Draw = namedtuple("Draw", ["id", "numbers"])
    results = main(Draw)
    print(results)
