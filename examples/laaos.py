import json
import blackhc.notebook
import prettyprinter
import functools
import operator
import itertools

from implicit_lambda import call, contains
from teddy import *

from data import laaos_data


pprint = functools.partial(prettyprinter.pprint, max_seq_len=20)

pprint(laaos_data.store)


pprint(teddy(laaos_data.store).iterations[:].num_epochs)
pprint(teddy(laaos_data.store).iterations[:].test_metrics[:])
pprint(teddy(laaos_data.store).iterations[:]["num_epochs", "test_metrics"])
