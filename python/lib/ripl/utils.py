# Copyright (c) 2013, MIT Probabilistic Computing Project.
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
# You should have received a copy of the GNU General Public License along with Venture.  If not, see <http://www.gnu.org/licenses/>.
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from venture.exception import VentureException

# This list of functions defines the public REST API
# of the Ripl server and client
#
# could have used inspection to generate this list
# of functions, but being explicit is better/more secure
_RIPL_FUNCTIONS = [
        'get_mode','list_available_modes','set_mode',
        'execute_instruction','execute_program','substitute_params',
        'split_program','get_text','character_index_to_expression_index',
        'expression_index_to_text_index','assume','predict',
        'observe','configure','forget','report','infer',
        'clear','rollback','list_directives','get_directive',
        'force','sample','continuous_inference_status',
        'start_continuous_inference','stop_continuous_inference',
        'get_current_exception','get_state','get_logscore',
        'get_global_logscore'
        ]

def run_venture_console(ripl):
  done = False
  while not(done):
    sys.stdout.write('>>> ')
    current_line = sys.stdin.readline()
    current_line = current_line.strip()
    # TODO Provide for graceful exit
    if current_line[0] == "(":
      current_line = current_line[1:-1]
    if current_line[0] == "[":
      current_line = current_line[1:-1]
    current_line = current_line.split(" ", 1)
    directive_name = current_line[0].lower()
    sys.stdout.write('')
    try:
      if (directive_name == "quit"):
        print "Moriturus te saluto."
        done = True
      elif (directive_name == "list-directives"):
        for d in ripl.list_directives():
          print d
      elif (directive_name == "get-global-log-score"):
        print ripl.get_global_logscore()
      elif (directive_name == "continuous-inference-status"):
        print ripl.continuous_inference_status()
      elif (directive_name == "start-continuous-inference"):
        ripl.start_continuous_inference()
        print ripl.continuous_inference_status()
      elif (directive_name == "stop-continuous-inference"):
        ripl.stop_continuous_inference()
        print ripl.continuous_inference_status()
      else:
        content = current_line[1]
        if (directive_name == "assume"):
          name_and_expression = content.split(" ", 1)
          print ripl.assume(name_and_expression[0], name_and_expression[1])
        elif (directive_name == "predict"):
          print ripl.predict(content)
        elif (directive_name == "observe"):
          expression_and_literal_value = content.rsplit(" ", 1)
          ripl.observe(expression_and_literal_value[0], expression_and_literal_value[1])
        elif (directive_name == "forget"):
          ripl.forget(int(content))
          print "Forgotten directive # {0}.".format(content)
        elif (directive_name == "sample"):
          print ripl.sample(content)
        elif (directive_name == "force"):
          expression_and_literal_value = content.rsplit(" ", 1)
          ripl.force(expression_and_literal_value[0], expression_and_literal_value[1])
        elif (directive_name == "infer"):
          ripl.infer(int(content))
          print "Made {0} inference iterations.".format(content)
        elif (directive_name == "report"):
          print ripl.report(int(content))
        elif (directive_name == "clear"):
          ripl.clear()
          print "Cleared trace."
        else:
          print "Sorry, unknown directive."
    except Exception, err:
      print "Your query has generated an error: " + str(err)

