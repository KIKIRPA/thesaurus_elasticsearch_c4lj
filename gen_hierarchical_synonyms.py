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


def generate_hierarchical(graph, output):
    h = {}
    qres = graph.query("""
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        PREFIX thesau: <http://hescida.kikirpa.be/thesau/skos/term#>

        SELECT ?term ?prefLab (count(?middle)-1 as ?distance) WHERE {
          ?category skos:prefLabel ?term ;
                    skos:narrower* ?middle .
          ?middle skos:narrower* ?concept .
          ?concept skos:prefLabel ?prefLab .
        }
        GROUP BY ?term ?prefLab
        ORDER BY ?term ?prefLab
    """)
    print(f"We have {len(qres)} results when processing narrower terms.")

    for row in qres:
        if 0 < int(row[2]) < 4:
            term1 = synonym_cleaning(row[0])
            term2 = synonym_cleaning(row[1])
            h.setdefault(term1, {"narrower": []})["narrower"].append(term2)

    with Path(output).open(mode="w") as outfile:
        for k in h:
            terms = {
                term: None for term in list([
                    *h[k].get('narrower', []),
                    k
                ])
            }
            if len(terms.keys()) > 1:
                outfile.write(f"{k} => {', '.join(terms.keys())}\n")


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
        '-H', '--hierarchical',
        help="Specifiy the filename where to output hierarchical synonyms.",
        required=True
    )
    args = parser.parse_args()

    graph = Graph().parse(args.skos, format='turtle')

    generate_hierarchical(graph, args.hierarchical)

    return 0


if __name__ == '__main__':
    exit(main())
