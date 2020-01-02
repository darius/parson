"""
Parse by interpreting a compiled VM
"""

from structs import Visitor
from ebnf import Grammar

def compile_grammar(grammar):
    labels = {}
    insns = []
    for name in grammar.nonterminals:
        labels[name] = len(insns)
        insns.extend(compiling(grammar.directed[name]))
        insns.append(('return', None))
    # TODO: make sure the client knows about grammar.errors
    return Code(insns, labels, grammar.actions)

class Code(object):
    def __init__(self, insns, labels, actions):
        self.insns = insns
        self.labels = labels
        self.actions = actions
        self.label_of_addr = dict(zip(labels.values(), labels.keys()))

    def show(self):
        for pc in range(len(self.insns)):
            self.show_insn(pc)

    def show_insn(self, pc):
        label = self.label_of_addr.get(pc, '')
        op, arg = self.insns[pc]
        if op == 'return':
            arg = ''
        elif op == 'branch':
            cases, default = arg
            cases = [(','.join(sorted(s.text for s in kinds)), dest)
                     for kinds, dest in cases]
            arg = cases, default
        print '%-10s %3d %-6s %r' % (label, pc, op, arg)

    def parse(self, tokens, start='start'):
        limit = 100
        tokens = list(tokens) + [None]  # EOF sentinel
        i = 0
        frames = [[]]
        return_stack = [None]
        pc = self.labels[start]
        print 'starting', pc
        while pc is not None:
            limit -= 1
            if limit <= 0: break
            print ' '*50, zip(return_stack, frames)
            self.show_insn(pc)
            op, arg = self.insns[pc]
            pc += 1
            if op == 'call':
                frames.append([])
                return_stack.append(pc)
                pc = self.labels[arg]
            elif op == 'return':
                pc = return_stack.pop()
                results = frames.pop()
                if pc is None:
                    return results
                frames[-1].extend(results)
            elif op == 'eat':
                if tokens[i] == arg.text:
                    i += 1
                else:
                    raise SyntaxError("Missing %r" % arg)
            elif op == 'branch':
                cases, default = arg
                for kinds, dest in cases:
                    if tokens[i] in [s.text for s in kinds]: # XXX awkward
                        pc += dest
                        break
                else:
                    pc += default
            elif op == 'jump':
                pc += arg
            elif op == 'act':
                action = self.actions[arg]
                frame = frames[-1]
                frame[:] = [action(*frame)]
            elif op == 'fail':
                raise SyntaxError("Unexpected token %r; expecting one of %r"
                                  % (tokens[i], sorted(arg)))
            else:
                assert False

class Compiling(Visitor):
    def Empty(self, t):  return []
    def Symbol(self, t): return [('eat', t)]
    def Call(self, t):   return [('call', t.name)]
    def Branch(self, t): return compile_branch(t)
    def Fail(self, t):   return [('fail', t.possibles)]
    def Chain(self, t):  return self(t.e1) + self(t.e2)
    def Loop(self, t):   return compile_loop(t)
    def Action(self, t): return [('act', t.name)]
compiling = Compiling()

def compile_branch(t):
    cases = []
    insns = []
    fixups = []
    for kinds, alt in t.cases:
        dest = len(insns)       # Offset from the branch insn
        cases.append((kinds, dest))
        insns.extend(compiling(alt))
        fixups.append(len(insns))
        insns.append(None)      # to be fixed up
    default = len(insns)        # Offset from the branch insn
    insns.extend(compiling(t.default))
    for addr in fixups:
        insns[addr] = ('jump', len(insns) - (addr + 1)) # Skip to the common exit point
    insns.insert(0, ('branch', (cases, default)))
    return insns

def compile_loop(t):
    body = compiling(t.body)
    return ([('branch', ([(t.firsts, 0)], len(body)+1))]
            + body
            + [('jump', -len(body)-2)])


# Smoke test

## from ebnf import eg
## import operator
## actions = dict(X=lambda: 3, **operator.__dict__)
## egg = Grammar(eg, actions)

## egc = compile_grammar(egg)
## egc.show()
#. A            0 branch ([('b', 0), ('y', 4)], 6)
#.              1 call   'B'
#.              2 eat    Symbol('x', 'literal')
#.              3 call   'A'
#.              4 jump   3
#.              5 eat    Symbol('y', 'literal')
#.              6 jump   1
#.              7 fail   frozenset([Symbol('b', 'literal'), Symbol('y', 'literal')])
#.              8 return ''
#. B            9 eat    Symbol('b', 'literal')
#.             10 return ''
#. C           11 return ''
#. exp         12 call   'term'
#.             13 branch ([('+', 0), ('-', 4)], 8)
#.             14 eat    Symbol('+', 'literal')
#.             15 call   'exp'
#.             16 act    'add'
#.             17 jump   4
#.             18 eat    Symbol('-', 'literal')
#.             19 call   'exp'
#.             20 act    'sub'
#.             21 jump   0
#.             22 return ''
#. term        23 call   'factor'
#.             24 branch ([('*', 0)], 4)
#.             25 eat    Symbol('*', 'literal')
#.             26 call   'factor'
#.             27 act    'mul'
#.             28 jump   -5
#.             29 return ''
#. factor      30 branch ([('x', 0), ('(', 3)], 7)
#.             31 eat    Symbol('x', 'literal')
#.             32 act    'X'
#.             33 jump   5
#.             34 eat    Symbol('(', 'literal')
#.             35 call   'exp'
#.             36 eat    Symbol(')', 'literal')
#.             37 jump   1
#.             38 fail   frozenset([Symbol('x', 'literal'), Symbol('(', 'literal')])
#.             39 return ''
### egc.parse("x", start='exp')
### egc.parse("x+x-x", start='exp')
### egc.parse("x+(x*x+x)", start='exp')
