from unittest import TestCase
import statistics as stats

class TestCreateEventsClusters(TestCase):
    def setUp(self):
        """
        This method is called before each test
        """
        self.eventsTagsPairList = [[[['A', 'B']], 0], [[['B', 'C']], 0], [[['D', 'A']], 0], [[['G', 'F']], 0],
                              [[['Z', 'G']], 0], [[['C', 'S']], 0]]
        self.eventsTagsPairList2 = [[[['A', 'B']], 0], [[['B', 'C']], 0], [[['D', 'A']], 0], [[['F', 'D']], 0],
                                   [[['Z', 'G']], 0], [[['C', 'S']], 0], [[['W', 'Z']], 0], [[['P', 'T']], 0]]

    def tearDown(self):
        """
        This method is called after each test
        """
        pass

    def test_createEventsClusters(self):
        result = stats.createEventsClusters(self.eventsTagsPairList)
        expected = [[[['D', 'A'], ['A', 'B'], ['B', 'C'], ['C', 'S']], 0], [[['Z', 'G'], ['G', 'F']], 0]]
        self.assertEqual(result, expected)
        expected2 = [[[['F', 'D'], ['D', 'A'], ['A', 'B'], ['B', 'C'], ['C', 'S']], 0], [[['W', 'Z'], ['Z', 'G']], 0],
         [[['P', 'T']], 0]]
        result = stats.createEventsClusters(self.eventsTagsPairList2)
        self.assertEqual(result, expected2)