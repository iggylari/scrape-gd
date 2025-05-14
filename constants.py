QUERIES = [
    'data-engineer-jobs-SRCH_KO0,13.htm',
    'software-engineer-jobs-SRCH_KO0,18.htm',
    'analytics-engineer-jobs-SRCH_KO0,19.htm'
]

SITES = [
    ("www.glassdoor.ie", "IE", QUERIES),
    ("www.glassdoor.de", "DE", QUERIES),
    ("www.glassdoor.fr", "FR", QUERIES),
    ("www.glassdoor.co.uk", "UK", QUERIES),
    ("www.glassdoor.nl", "NL", QUERIES),
    ("www.glassdoor.nl", "BE", [
        "belgium-data-engineer-jobs-SRCH_IL.0,7_IN25_KO8,21.htm",
        "belgium-software-engineer-jobs-SRCH_IL.0,7_IN25_KO8,25.htm",
        "belgium-analytics-engineer-jobs-SRCH_IL.0,7_IN25_KO8,26.htm"
    ]),
    ("www.glassdoor.com", "FI", [
        "finland-data-engineer-jobs-SRCH_IL.0,7_IN79_KO8,21.htm",
        "finland-software-engineer-jobs-SRCH_IL.0,7_IN79_KO8,25.htm",
        "finland-analytics-engineer-jobs-SRCH_IL.0,7_IN79_KO8,26.htm"
    ])
]

DB_PATH = 'glassdoor.duckdb'
