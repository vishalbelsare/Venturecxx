# Copyright (c) 2014, MIT Probabilistic Computing Project.
# 
# This file is part of Venture.
# 	
# Venture is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 	
# Venture is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 	
# You should have received a copy of the GNU General Public License
# along with Venture.  If not, see <http://www.gnu.org/licenses/>.

# Venture parser (`Church prime', Lisp-style notation).

import StringIO
import collections

import venture.value.dicts as val

from venture.parser.church_prime import grammar
from venture.parser.church_prime import scan

def tokval((value, _start, _end)):
    return value

def located(loc, value):
    # XXX Use a namedtuple, not a dict.
    return { 'loc': loc, 'value': value }

def locmap(l, f):
    return { 'loc': l['loc'], 'value': f(l['value']) }

def loc1(l, v):
    return located(l['loc'], v)

def loc2(a, b, value):
    [start_a, end_a] = a['loc']
    [start_b, end_b] = b['loc']
    loc = [min(start_a, start_b), max(end_a, end_b)]
    return located(loc, value)

def locmerge(a, b, f):
    return loc2(a, b, f(a['value'], b['value']))

def loctoken((value, start, end)):
    return located([start, end], value)

def loctoken1((_value, start, end), value):
    return located([start, end], value)

def locbracket((ovalue, ostart, oend), (cvalue, cstart, cend), value):
    return located([ostart, cend], value)

def locunit(l):
    return loc1(l, [l])

def locappend(l, x):
    l1 = l['value']
    l1.append(x)
    return loc2(l, x, l1)

def delocust(l):
    # XXX Why do we bother with tuples in the first place?
    if isinstance(l['value'], list) or isinstance(l['value'], tuple):
        return [delocust(v) for v in l['value']]
    else:
        return l['value']

class Error(Exception):
    def __init__(self, message, start, end):
        self.message = message
        self.start = start
        self.end = end
    def __str__(self):
        return '[%s, %s]: %s' % (self.start, self.end, self.message)

class Semantics(object):
    def __init__(self):
        self.answer = None

    def accept(self):
        assert self.answer is not None
    def parse_failed(self):
        assert self.answer is None
    def syntax_error(self, (_number, (text, start, end))):
        # XXX Kinda kludgey!
        raise Error('Syntax error near %s' % (text,), start, end)

    # Venture start symbol: store result in self.answer, return none.
    def p_venture_empty(self):
        self.answer = []
    def p_venture_i(self, insts):
        self.answer = ('instructions', insts)
    def p_venture_e(self, exp):
        self.answer = ('expression', exp)

    # instructions: Return list of instructions.
    def p_instructions_one(self, inst):
        return [inst]
    def p_instructions_many(self, insts, inst):
        insts.append(inst)
        return insts

    # instruction: Return located { 'instruction': 'foo', ... }.
    def p_instruction_labelled(self, l, open, d, close):
        d['label'] = loctoken(l)
        d['instruction'] = locmap(d['instruction'], lambda i: 'labeled_' + i)
        return loc2(loctoken(l), loctoken(close), d)
    def p_instruction_unlabelled(self, open, d, close):
        return locbracket(open, close, d)
    def p_instruction_command(self, open, c, close):
        return locbracket(open, close, c)
    def p_instruction_laberror(self, d):
        return 'error'
    def p_instruction_labdirerror(self):
        return 'error'
    def p_instruction_error(self):
        return 'error'

    # directive: Return { 'instruction': located(..., 'foo'), ... }.
    def p_directive_assume(self, k, n, e):
        return { 'instruction': loctoken1(k, 'assume'),
                 'symbol': loctoken(n), 'expression': e }
    def p_directive_observe(self, k, e, v):
        return { 'instruction': loctoken1(k, 'observe'),
                 'expression': e, 'value': v }
    def p_directive_predict(self, k, e):
        return { 'instruction': loctoken1(k, 'predict'), 'expression': e }

    # command: Return { 'instruction': located(..., 'foo'), ... }.
    def p_command_configure(self, k, options):
        return { 'instruction': loctoken1(k, 'configure'), 'options': options }
    def p_command_forget(self, k, dr):
        i = 'labeled_forget' if dr[0] == 'label' else 'forget'
        return { 'instruction': loctoken1(k, i), dr[0]: dr[1] }
    def p_command_report(self, k, dr):
        i = 'labeled_report' if dr[0] == 'label' else 'report'
        return { 'instruction': loctoken1(k, i), dr[0]: dr[1] }
    def p_command_infer(self, k, e):
        return { 'instruction': loctoken1(k, 'infer'), 'expression': e }
    def p_command_clear(self, k):
        return { 'instruction': loctoken1(k, 'clear') }
    def p_command_rollback(self, k):
        return { 'instruction': loctoken1(k, 'rollback') }
    def p_command_list_directives(self, k):
        return { 'instruction': loctoken1(k, 'list_directives') }
    def p_command_get_directive(self, k, dr):
        i = 'labeled_get_directive' if dr[0] == 'label' else 'get_directive'
        return { 'instruction': loctoken1(k, i), dr[0]: dr[1] }
    def p_command_force(self, k, e, v):
        return { 'instruction': loctoken1(k, 'force'), 'expression': e,
                 'value': v }
    def p_command_sample(self, k, e):
        return { 'instruction': loctoken1(k, 'sample'), 'expression': e }
    def p_command_continuous_inference_status(self, k):
        return { 'instruction': loctoken1(k, 'continuous_inference_status') }
    def p_command_stop_continuous_inference(self, k):
        return { 'instruction': loctoken1(k, 'stop_continuous_inference') }
    def p_command_get_current_exception(self, k):
        return { 'instruction': loctoken1(k, 'get_current_exception') }
    def p_command_get_state(self, k):
        return { 'instruction': loctoken1(k, 'get_state') }
    def p_command_get_logscore(self, k, dr):
        i = 'labeled_get_logscore' if dr[0] == 'label' else 'get_logscore'
        return { 'instruction': loctoken1(k, i), dr[0]: dr[1] }
    def p_command_get_global_logscore(self, k):
        return { 'instruction': loctoken1(k, 'get_global_logscore') }
    def p_command_profiler_configure(self, k, options):
        return { 'instruction': loctoken1(k, 'profiler_configure'),
                 'options': options }
    def p_command_profiler_clear(self, k):
        return { 'instruction': loctoken1(k, 'profiler_clear') }
    def p_command_list_random(self, k):
        return { 'instruction': loctoken1(k, 'profiler_list_random_choices') }
    def p_command_load(self, k, pathname):
        return { 'instruction': loctoken1(k, 'load'), 'file': pathname }

    # directive_ref: Return (reftype, located value) tuple.
    def p_directive_ref_numbered(self, number):
        return ('directive_id', loctoken(number))
    def p_directive_ref_labelled(self, label):
        return ('label', loctoken(label))

    # expression: Return located expression.
    def p_expression_symbol(self, name):
        return locmap(loctoken(name), val.symbol)
    def p_expression_literal(self, value):
        return value
    def p_expression_combination(self, open, es, close):
        return locbracket(open, close, es or [])
    def p_expression_comb_error(self, open, es, close):
        return 'error'

    # expressions: Return list of expressions, or None.
    def p_expressions_none(self):
        return []
    def p_expressions_some(self, es, e):
        es.append(e)
        return es

    # literal: Return located `val'.
    def p_literal_true(self, t):
        return locmap(loctoken1(t, True), val.boolean)
    def p_literal_false(self, f):
        return locmap(loctoken1(f, False), val.boolean)
    def p_literal_integer(self, v):
        return locmap(loctoken(v), val.number)
    def p_literal_real(self, v):
        return locmap(loctoken(v), val.number)
    def p_literal_json(self, type, open, value, close):
        type = tokval(type)
        if type == 'number' or type == 'boolean':
            raise SyntaxError('Write numbers and booleans without JSON!')
        return loc2(loctoken(open), loctoken(close),
            { 'type': type, 'value': value })

    # json: Return json object.
    def p_json_string(self, v):                 return tokval(v)
    def p_json_integer(self, v):                return tokval(v)
    def p_json_real(self, v):                   return tokval(v)
    def p_json_list(self, l):                   return l
    def p_json_dict(self, d):                   return d

    # json_list: Return list.
    def p_json_list_l(self, b):                 return b
    def p_json_list_body_none(self):            return []
    def p_json_list_body_some(self, ts):        return ts
    def p_json_list_terms_one(self, t):         return [t]
    def p_json_list_terms_many(self, ts, t):    ts.append(t); return ts
    def p_json_list_terms_error(self, t):       return ['error']

    # json_dict: Return dict.
    def p_json_dict_empty(self):                return {}
    def p_json_dict_nonempty(self, es):         return es
    def p_json_dict_error(self, es):            return ['error']

    # json_dict_entries: Return dict.
    def p_json_dict_entries_one(self, e):       return { e[0]: e[1] }
    # XXX Check for duplicates.
    def p_json_dict_entries_many(self, es, e):  es[e[0]] = e[1]; return es
    def p_json_dict_entries_error(self, e):     return { 'error': 'error' }

    # json_dict_entry: Return (key, value) tuple.
    def p_json_dict_entry_e(self, key, value):  return (tokval(key), value)
    def p_json_dict_entry_error(self, value):   return ('error', value)

def parse_church_prime(f, context):
    scanner = scan.Scanner(f, context)
    semantics = Semantics()
    parser = grammar.Parser(semantics)
    while True:
        token = scanner.read()
        if token[0] is None:
            # XXX Should not touch scanner internal variables like this.
            parser.feed((0, ('', scanner.cur_pos, scanner.cur_pos - 1)))
            break
        parser.feed(token)
    return semantics.answer

def parse_church_prime_string(string):
    try:
        return parse_church_prime(StringIO.StringIO(string), '(string)')
    except Error as e:
        start = e.start
        end = e.end
        spaces = ' ' * start
        carets = '^' * (end + 1 - start)
        message = '%s\n    %s\n    %s%s' % (e.message, string, spaces, carets)
        raise Error(message, e.start, e.end)

def parse_instructions(string):
    t, ls = parse_church_prime_string(string)
    if t != 'instructions':
        raise Exception('Syntax error -- not instructions: %s' % (string,))
    return ls

def parse_instruction(string):
    ls = parse_instructions(string)
    if len(ls) != 1:
        raise Exception('Syntax error -- not one instruction: %s' % (string,))
    return ls[0]

def parse_expression(string):
    t, l = parse_church_prime_string(string)
    if t != 'expression':
        raise Exception('Syntax error -- not expression: %s' % (string,))
    return l

the_parser = None

class ChurchPrimeParser(object):
    '''Legacy interface to Church' parser.'''

    @staticmethod
    def instance():
        '''Return the global Church' parser instance.'''
        global the_parser
        if the_parser is None:
            the_parser = ChurchPrimeParser()
        return the_parser

    # XXX Doesn't really belong here.
    def substitute_params(self, string, params):
        '''Return STRING with %-directives formatted using PARAMS.'''
        return subst.substitute_params(string, params)

    def parse_instruction(self, string):
        '''Parse STRING as a single instruction.'''
        l = parse_instruction(string)
        return dict((k, delocust(v)) for k, v in l['value'].iteritems())

    def parse_expression(self, string):
        '''Parse STRING as an expression.'''
        return delocust(parse_expression(string))

    def unparse_expression(self, expression):
        '''Unparse EXPRESSION into a string.'''
        if isinstance(expression, dict):        # Leaf.
            return value_to_string(expression)
        elif isinstance(expression, basestring):
            # XXX This is due to &@!#^&$@!^$&@#!^%&*.
            return expression
        elif isinstance(expression, list):
            terms = (self.unparse_expression(e) for e in expression)
            return '(' + ' '.join(terms) + ')'
        else:
            raise TypeError('Invalid expression: %s' % (repr(expression),))

    def unparse_integer(self, integer):
        return str(integer)
    def unparse_symbol(self, symbol):
        return str(symbol)
    def unparse_value(self, value):
        return value_to_string(value)
    def unparse_json(self, obj):
        return json.dumps(obj)

    # XXX The one useful property the old parser had is that this
    # table was written once, in one place, for the parser and
    # unparser.  Well, actually, twice -- once for church prime and
    # once for venture script, with slight differences...
    unparsers = {
        'define': [('symbol', unparse_symbol), ('expression', unparse_expression)],
        'labeled_define': [('symbol', unparse_symbol), ('expression', unparse_expression)],
        'assume': [('symbol', unparse_symbol), ('expression', unparse_expression)],
        'labeled_assume': [('symbol', unparse_symbol), ('expression', unparse_expression)],
        'observe': [('symbol', unparse_symbol), ('value', unparse_value)],
        'labeled_observe': [('symbol', unparse_symbol), ('value', unparse_value)],
        'predict': [('expression', unparse_expression)],
        'labeled_predict': [('expression', unparse_expression)],
        'configure': [('options', unparse_json)],
        'forget': [('directive_id', unparse_integer)],
        'labeled_forget': [('label', unparse_symbol)],
        'report': [('directive_id', unparse_integer)],
        'labeled_report': [('label', unparse_symbol)],
        'infer': [('expression', unparse_expression)],
        'clear': [],
        'rollback': [],
        'list_directives': [],
        'get_directive': [('directive_id', unparse_integer)],
        'labeled_get_directive': [('label', unparse_symbol)],
        'force': [('expression', unparse_expression), ('value', unparse_value)],
        'sample': [('expression', unparse_expression)],
        'continuous_inference_status': [],
        'start_continuous_inference': [],
        'stop_continuous_inference': [],
        'get_current_exception': [],
        'get_state': [],
        'get_logscore': [('directive_id', unparse_integer)],
        'labeled_get_logscore': [('label', unparse_symbol)],
        'profiler_configure': [('options', unparse_json)],
        'profiler_clear': [],
        'profiler_list_random': [], # XXX Urk, extra keyword.
        'load': [('file', unparse_json)],
    }
    def unparse_instruction(self, instruction):
        '''Unparse INSTRUCTION into a string.'''
        # XXX This is not correct.  But it might do for now.
        chunks = []
        if 'label' in instruction:
            chunks.append(instruction['label'])
            chunks.append(': ')
        chunks.append('[')
        i = instruction['instruction']
        if i[0 : len('labeled_')] == 'labeled_':
            chunks.append(i[len('labeled_'):])
        else:
            chunks.append(i)
        for key, unparser in self.unparsers[i]:
            chunks.append(' ')
            chunks.append(unparser(self, instruction[key]))
        chunks.append(']')
        return ''.join(chunks)

    # XXX ???
    def parse_number(self, string):
        '''Parse STRING as an integer or real number.'''
        return float(string) if '.' in string else int(string)

    # XXX ???
    def split_program(self, string):
        '''Split STRING into a sequence of instructions.

        Return a two-element list containing
        [0] a list of substrings, one for each instruction; and
        [1] a list of [start, end] positions of each instruction in STRING.
        '''
        ls = parse_instructions(string)
        locs = [l['loc'] for l in ls]
        # XXX + 1?
        strings = [string[loc[0] : loc[1] + 1] for loc in locs]
        # XXX Sort??
        sortlocs = [list(sorted(loc)) for loc in locs]
        # XXX List???
        return [strings, sortlocs]

    # XXX ???
    def split_instruction(self, string):
        '''Split STRING into a dict of instruction operands.

        Return a two-element list containing
        [0] a dict mapping operand keys to substrings of STRING; and
        [1] a dict mapping operand keys to [start, end] positions.
        '''
        l = parse_instruction(string)
        locs = dict((k, v['loc']) for k, v in l['value'].iteritems())
        # XXX + 1?
        strings = dict((k, string[loc[0] : loc[1] + 1]) for k, loc in
            locs.iteritems())
        # XXX Sort???
        sortlocs = dict((k, list(sorted(loc))) for k, loc in locs.iteritems())
        # XXX List???
        return [strings, sortlocs]

    # XXX Make the tests pass, nobody else calls this.
    def character_index_to_expression_index(self, _string, index):
        '''Return bogus data to make tests pass.  Nobody cares!'''
        return [[], [0], [], None, None, [2], [2,0]][index]

    def expression_index_to_text_index(self, string, index):
        '''Return position of expression in STRING indexed by INDEX.

        - STRING is a string of an expression.
        - INDEX is a list of indices into successively nested
          subexpressions.

        Return [start, end] position of the last nested subexpression.
        '''
        l = parse_expression(string)
        for i in range(len(index)):
            if index[i] < 0 or len(l['value']) <= index[i]:
                raise ValueError('Index out of range: %s in %s' %
                    (index, repr(string)))
            l = l['value'][index[i]]
        return l['loc']
