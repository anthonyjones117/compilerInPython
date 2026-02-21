
def skip_space(s, idx):
    while True:
        save = idx
        # try to skip spaces
        while idx < len(s) and s[idx].isspace():
            idx += 1
        # try to skip a line comment
        if idx < len(s) and s[idx] == ';':
            idx += 1
            while idx < len(s) and s[idx] != '\n':
                idx += 1
        # no more spaces or comments
        if idx == save:
            break
    return idx

def pl_parse(s):
    idx, node = parse_expr(s, 0)
    idx = skip_space(s, idx)
    if idx < len(s):
        raise ValueError('trailing garbage')
    return node

# bool, number, string or a symbol
def parse_atom(s):
    # TODO: actually implement this
    import json
    try:
        return ['val', json.loads(s)]
    except json.JSONDecodeError:
        return s

def parse_expr(s: str, idx: int):
    idx = skip_space(s, idx)
    if s[idx] == '(':
        # a list
        idx += 1
        l = []
        while True:
            idx = skip_space(s, idx)
            if idx >= len(s):
                raise Exception('unbalanced parenthesis')
            if s[idx] == ')':
                idx += 1
                break

            idx, v = parse_expr(s, idx)
            l.append(v)
        return idx, l
    elif s[idx] == ')':
        raise Exception('bad parenthesis')
    else:
        # an atom
        start = idx
        while idx < len(s) and (not s[idx].isspace()) and s[idx] not in '()':
            idx += 1
        if start == idx:
            raise Exception('empty program')
        return idx, parse_atom(s[start:idx])
    
def name_loopup(env, key):
    while env:  # linked list traversal
        current, env = env
        if key in current:
            return current
    raise ValueError('undefined name')

def pl_parse_prog(s):
    return pl_parse('(do ' + s + ')')

def pl_eval(env, node):

    # read a variable
    if not isinstance(node, list):
        assert isinstance(node, str)
        return name_loopup(env, node)[node]
    
    if len(node) == 0:
        raise ValueError('empty list')

    # bool, number, string and etc
    if len(node) == 2 and node[0] == 'val':
        return node[1]

    # binary operators
    import operator
    binops = {
        '+': operator.add,
        '-': operator.sub,
        '*': operator.mul,
        '/': operator.truediv,
        'eq': operator.eq,
        'ne': operator.ne,
        'ge': operator.ge,
        'gt': operator.gt,
        'le': operator.le,
        'lt': operator.lt,
        'and': operator.and_,
        'or': operator.or_,
    }
    if len(node) == 3 and node[0] in binops:
        op = binops[node[0]]
        return op(pl_eval(env, node[1]), pl_eval(env, node[2]))

    # unary operators
    unops = {
        '-': operator.neg,
        'not': operator.not_,
    }
    if len(node) == 2 and node[0] in unops:
        op = unops[node[0]]
        return op(pl_eval(env, node[1]))

    # conditional
    if len(node) in (3, 4) and node[0] in ('?', 'if'):
        _, cond, yes, *no = node
        no = no[0] if no else ['val', None] # the `else` part is optional
        new_env = (dict(), env) # new scope
        if pl_eval(new_env, cond):
            return pl_eval(new_env, yes)
        else:
            return pl_eval(new_env, no)

    # print
    if node[0] == 'print':
        return print(*(pl_eval(env, val) for val in node[1:]))
    
    # new scope
    if node[0] in ('do', 'then', 'else') and len(node) > 1:
        new_env = (dict(), env) # add the map as the linked list head
        for val in node[1:]:
            val = pl_eval(new_env, val)
        return val  # the last item
    
    # new variable
    if node[0] == 'var' and len(node) == 3:
        _, name, val = node
        scope, _ = env
        if name in scope:
            raise ValueError('duplicated name')
        val = pl_eval(env, val)
        scope[name] = val
        return val
    
    # update a variable
    if node[0] == 'set' and len(node) == 3:
        _, name, val = node
        scope = name_loopup(env, name)
        val = pl_eval(env, val)
        scope[name] = val
        return val
    
    # loop
    if node[0] == 'loop' and len(node) == 3:
        _, cond, body = node
        ret = None
        while True:
            new_env = (dict(), env)
            if not pl_eval(new_env, cond):
                break
            ret = pl_eval(new_env, body)
        return ret

    # conditional
    if len(node) in (3, 4) and node[0] in ('?', 'if'):
        _, cond, yes, *no = node
        no = no[0] if no else ['val', None] # the `else` part is optional
        new_env = (dict(), env) # new scope
        if pl_eval(new_env, cond):
            return pl_eval(new_env, yes)
        else:
            return pl_eval(new_env, no)

    raise ValueError('unknown expression')

def test_eval():
    def f(s):
        return pl_eval( (dict(),None), pl_parse_prog(s))

    assert f('''
        ;; first scope
        (var a 1)
        (var b (+ a 1))
        ;; a=1, b=2
        (do
            ;; new scope
            (var a (+ b 5))     ;; name collision
            (set b (+ a 10))
        )
        ;; a=1, b=17
        (* a b)
    ''') == 17

def main():
    test_eval()

if __name__ == "__main__":
    main()
