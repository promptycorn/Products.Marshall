# Marshall: A framework for pluggable marshalling policies
# Copyright (C) 2004-2006 Enfold Systems, LLC
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
"""
"""

import re
import difflib
import unittest

from plone.app.testing import (PLONE_FIXTURE, PloneSandboxLayer,
                               IntegrationTesting, FunctionalTesting,
                               SITE_OWNER_NAME)
from plone.testing import zope


class MarshallLayer(PloneSandboxLayer):
    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        import Products.Marshall
        self.loadZCML('configure.zcml', package=Products.Marshall)
        zope.installProduct(app, 'Products.Marshall')


MARSHALL_FIXTURE = MarshallLayer()
INTEGRATION_TESTING = IntegrationTesting(bases=(MARSHALL_FIXTURE,),
                                        name='Marshall:Integration')
FUNCTIONAL_TESTING = FunctionalTesting(bases=(MARSHALL_FIXTURE,),
                                      name='Marshall:Functional')


def normalize_tabs(s):
    s = re.sub(r"[ \t]+", " ", s)
    return s


def normalize_space(s):
    s =  re.sub(r"[\r\n]+", r'\r\n', s)
    return s


class BaseTest(unittest.TestCase):
    """Base Test"""
    layer = INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.afterSetUp()

    def afterSetUp(self):
        pass

    def loginAsPortalOwner(self):
        zope.login(self.layer['app']['acl_users'], SITE_OWNER_NAME)

    def compare(self, one, two):
        diff = difflib.ndiff(one.splitlines(), two.splitlines())
        diff = '\n'.join(list(diff))
        return diff

    def assertEqualsDiff(self, one, two, normalize=True):
        if isinstance(one, bytes):
            one = one.decode('utf-8')
        if isinstance(two, bytes):
            two = two.decode('utf-8')
        if normalize:
            one, two = normalize_tabs(one), normalize_tabs(two)
        one, two = normalize_space(one), normalize_space(two)
        self.assertTrue(one.splitlines() == two.splitlines(),
                        self.compare(one, two))
