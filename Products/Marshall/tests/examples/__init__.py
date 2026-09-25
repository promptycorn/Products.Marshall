# import this
from Products.Archetypes.public import listTypes, process_types

from . import person
from . import blob
process_types(listTypes('tests.Marshall'), 'tests.Marshall')
