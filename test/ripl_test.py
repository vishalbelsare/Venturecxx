import unittest
from venture.ripl import Ripl
from venture.exception import VentureException
from venture.sivm import VentureSIVM, CoreSIVMCppEngine
from venture.parser import ChurchPrimeParser

class TestRipl(unittest.TestCase):
    def setUp(self):
        self.core_sivm = CoreSIVMCppEngine()
        self.core_sivm.execute_instruction({"instruction":"clear"})
        self.venture_sivm = VentureSIVM(self.core_sivm)
        self.parser = ChurchPrimeParser()
        self.ripl = Ripl(self.venture_sivm,
                {"church_prime":self.parser,
                    "church_prime_2":self.parser})

    ############################################
    # Languages
    ############################################

    def test_modes(self):
        output = self.ripl.list_available_modes()
        self.assertEqual(set(output),set(['church_prime','church_prime_2']))
        self.ripl.set_mode('church_prime')
        output = self.ripl.get_mode()
        self.assertEqual(output,'church_prime')
        self.ripl.set_mode('church_prime_2')
        output = self.ripl.get_mode()
        self.assertEqual(output,'church_prime_2')
        with self.assertRaises(VentureException):
            self.ripl.set_mode("moo")

    ############################################
    # Execution
    ############################################

    def test_execute_instruction(self):
        f = self.ripl.execute_instruction
        f("[assume a 1]")
        f("[assume b (+ 1 2)]")
        f("[assume c (- b a)]")
        text_id, ret_value= f("[predict c]")
        self.assertEqual(ret_value['value'], {"type":"number","value":2})

    def test_execute_program(self):
        f = self.ripl.execute_program
        ret_value = f("[assume a 1] [assume b (+ 1 2)] [assume c (- b a)] [predict c]")
        self.assertEqual(ret_value[-1]['value'], {"type":"number","value":2})

    def test_parse_exception_sugaring(self):
        f = self.ripl.execute_instruction
        try:
            f("[assume a (+ (if 1 2) 3)]")
        except VentureException as e:
            self.assertEqual(e.data['text_index'], [13,20])
            self.assertEqual(e.exception, 'parse')

    def test_invalid_argument_exception_sugaring(self):
        f = self.ripl.execute_instruction
        try:
            f("[forget moo]")
        except VentureException as e:
            self.assertEqual(e.data['text_index'], [8,10])
            self.assertEqual(e.exception, 'invalid_argument')

    ############################################
    # Text manipulation
    ############################################

    def test_substitute_params(self):
        string = "a %s %j %v"
        params = ['b','2',2]
        expected_output = 'a b "2" 2'
        output = self.ripl.substitute_params(string,params)
        self.assertEqual(output, expected_output)

    def test_split_program(self):
        output = self.ripl.split_program(" [ force blah count<132>][ infer 132 ]")
        instructions = ['[ force blah count<132>]','[ infer 132 ]']
        indices = [[1,24],[25,37]]
        self.assertEqual(output,[instructions, indices])

    def test_get_text(self):
        self.ripl.set_mode('church_prime')
        text = "[assume a (+ (if true 2 3) 4)]"
        text_id, value = self.ripl.execute_instruction(text)
        output = self.ripl.get_text(text_id)
        self.assertEqual(output, ['church_prime',text])

    def test_directive_id_to_text_id(self):
        #TODO: write test when directive id functions implemented
        pass

    def test_text_id_to_directive_id(self):
        #TODO: write test when directive id functions implemented
        pass

    def test_character_index_to_expression_index(self):
        text = "[assume a (+ (if true 2 3) 4)]"
        text_id, value = self.ripl.execute_instruction(text)
        output = self.ripl.character_index_to_expression_index(text_id, 10)
        self.assertEqual(output, [])

    def test_expression_index_to_text_index(self):
        text = "[assume a (+ (if true 2 3) 4)]"
        text_id, value = self.ripl.execute_instruction(text)
        output = self.ripl.expression_index_to_text_index(text_id, [])
        self.assertEqual(output, [10,28])


    ############################################
    # Directives
    ############################################

    def test_assume(self):
        #normal assume
        ret_value = self.ripl.assume('c', '(+ 1 1)')
        self.assertEqual(ret_value, 2)
        #labeled assume
        ret_value = self.ripl.assume('d', '(+ 1 1)', 'moo')
        self.assertEqual(ret_value, 2)

    def test_predict(self):
        #normal predict
        ret_value = self.ripl.predict('(+ 1 1)')
        self.assertEqual(ret_value, 2)
        #labeled predict
        ret_value = self.ripl.predict('(+ 1 1)','moo')
        self.assertEqual(ret_value, 2)

    def test_observe(self):
        #normal observe
        self.ripl.assume('a','(uniform_continuous 0 1)')
        output = self.ripl.observe('a',0.5)
        self.assertEqual(output, None)
        output = self.ripl.predict('a')
        self.assertEqual(output, 0.5)
        #labeled observe
        self.ripl.observe('true','true','moo')

if __name__ == '__main__':
    unittest.main()
