#!/usr/bin/env python

import argparse
import re
from pathlib import Path

from rdflib import Graph


def _stripping_square_bracket(s):
    s = re.sub(r"\[[^\[\]]+]", "", s)

    return s


def _stripping_slashes(s):
    s = s.replace('/', ' ').replace('\\', ' ')

    return s


def _stripping_comma(s):
    s = s.replace(',', '')

    return s


def synonym_cleaning(synonym):
    actions = {
        'lowercase': str.lower,
        'strip_comma': _stripping_comma,
        'strip_square_bracket': _stripping_square_bracket,
        'strip_slashes': _stripping_slashes,
    }

    for action in actions:
        synonym = actions[action](synonym)

    return synonym


def generate_bilingual(graph, output):
    qres = graph.query("""
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        PREFIX thesaurus: <http://localhost/thesaurus/skos/term#>

        SELECT ?label ?equivalent WHERE { 
          ?term skos:prefLabel ?label ;
                skos:exactMatch ?concept .
          ?concept skos:prefLabel ?equivalent .
          FILTER((LANG(?label) = "fr" && LANG(?equivalent) = "nl") || (LANG(
          ?label) = "nl" && LANG(?equivalent) = "fr")) .
        }
    """)

    with Path(output).open(mode="w") as outfile:
        seen = {}
        for row in qres:
            term1 = synonym_cleaning(row[0])
            term2 = synonym_cleaning(row[1])

            if term1 != term2 and term1 not in seen and term2 not in seen:
                outfile.write(f"{str(term1)},{str(term2)}\n")
                seen.update({
                    term1: 1,
                    term2: 1
                })


def main():
    parser = argparse.ArgumentParser(
        description="Generating synonyms for Elasticsearch based on a SKOS file "
                    "(Turtle representation)."
    )

    parser.add_argument(
        '-s', '--skos',
        help="Specifiy the filename for the SKOS input (Turtle format).",
        required=True
    )
    parser.add_argument(
        '-b', '--bilingual',
        help="Specifiy the filename where to output bilingual synonyms.",
        required=True
    )
    args = parser.parse_args()

    graph = Graph().parse(args.skos, format='turtle')

    if args.bilingual:
        generate_bilingual(graph, args.bilingual)
        return 0
    else:
        return 1


if __name__ == '__main__':
    exit(main())
