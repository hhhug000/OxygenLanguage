import os
import re

# Exceptions so they can be detected and handled for loops and stuff
class ReturnException(Exception):
    def __init__(self, value):
        self.value = value

class BreakException(Exception):
    pass

class ContinueException(Exception):
    pass

# Run a single line of code, takes in context for code blocks and env for vars and all that
def runLine(line, context, index, env):
    if not line:
        return 1

    # get the command
    # command is the first token
    cmd = line[0]

    line = removeComments(line)

    # variable assignment, check if its a list or string index assignment
    if "=" in line:
        equalsIdx = line.index("=")
        leftSide = line[:equalsIdx]
        if len(leftSide) >= 4 and leftSide[1] == "[" and leftSide[-1] == "]":
            varName = leftSide[0]
            indexTokens = leftSide[2:-1]
            idx = int(evaluateExpression(indexTokens, env))
            # remember rhs is right hand side
            # so everything after equals
            rhsTokens = line[equalsIdx + 1:]
            val = evaluateExpression(rhsTokens, env)
            if varName in env:
                current_val = env[varName]
                if isinstance(current_val, str):
                    char_list = list(current_val)
                    char_list[idx] = str(val)
                    env[varName] = "".join(char_list)
                elif isinstance(current_val, list):
                    current_val[idx] = val
            return 1

    # variable assignment, check if its a list or string index assignment
    if len(line) >= 3 and line[1] == "=":
        varName = line[0]
        rhsTokens = line[2:]
        env[varName] = evaluateExpression(rhsTokens, env)
        return 1

    # All the commands (not vars and stuff)

    # print to console
    if cmd == "print":
        args = getArgsFromBrackets(line, env)
        print(*args)
        return 1
    # define a function, stored in env
    elif cmd == "def":
        funcName = line[1]

        # get the argument names, they are between brackets
        argTokens = []
        try:
            openBracket = line.index("(")
            closeBracket = line.index(")")
            argTokens = line[openBracket + 1:closeBracket]
        except ValueError:
            pass

        argNames = [token for token in argTokens if token != ","]

        # find the end of the function
        endIndex = index
        depth = 1
        while endIndex < len(context) - 1:
            endIndex += 1
            if context[endIndex]:
                if context[endIndex][0] in ("if", "while", "def"):
                    depth += 1
                elif context[endIndex][0] == "end":
                    depth -= 1
                    if depth == 0:
                        break

        # add to env
        env[funcName] = {
            "type": "function",
            "args": argNames,
            "startIndex": index + 1,
            "endIndex": endIndex,
            "context": context
        }

        return (endIndex - index) + 1

    # if statements
    # handled together with elif and else so they are in one block
    elif cmd == "if":
        # branches is a list of dicts with cond, start and end
        branches = []

        # get if statement condition
        try:
            thenIndex = line.index("then")
            currentCond = line[1:thenIndex]
        except ValueError:
            currentCond = line[1:]

        # find the end of the if statement and all elif and else branches
        branchStart = index + 1

        # loop through the context to find the end of the if statement and all elif and else branches
        i = index + 1
        depth = 1
        while i < len(context):
            curr = context[i]
            if curr:
                c = curr[0]
                if c in ("if", "while", "def"):
                    depth += 1
                elif c == "end":
                    if depth == 1:
                        branches.append({
                            "cond": currentCond,
                            "start": branchStart,
                            "end": i
                        })
                        break
                    else:
                        depth -= 1
                # create new branches for elif and else
                elif depth == 1 and c in ("elif", "else"):
                    branches.append({
                        "cond": currentCond,
                        "start": branchStart,
                        "end": i
                    })
                    if c == "elif":
                        try:
                            thenIdx = curr.index("then")
                            currentCond = curr[1:thenIdx]
                        except ValueError:
                            currentCond = curr[1:]
                    else:
                        currentCond = None
                    branchStart = i + 1
            i += 1

        # execute first branch thats true
        for b in branches:
            cond = b["cond"]
            if cond is None:
                executeBlock(context, b["start"], b["end"], env)
                break
            else:
                if bool(evaluateExpression(cond, env)):
                    executeBlock(context, b["start"], b["end"], env)
                    break

        return (i - index) + 1

    # while loops
    elif cmd == "while":
        # get all condition tokens, between command and do
        condTokens = line[1 : line.index("do")] if "do" in line else line[1:]

        endIndex = index
        depth = 1
        # find end of while to loop it
        while endIndex < len(context) - 1:
            endIndex += 1
            if context[endIndex]:
                if context[endIndex][0] in ("if", "while", "for", "def"):
                    depth += 1
                elif context[endIndex][0] == "end":
                    depth -= 1
                    if depth == 0:
                        break

        # eval expression
        while bool(evaluateExpression(condTokens, env)):
            i = index + 1
            try:
                while i < endIndex:
                    currLine = context[i]
                    if currLine:
                        res = runLine(currLine, context, i, env)
                        i += res if res is not None else 1
                    else:
                        i += 1
            # super cool exception method to catch and handle continue and break
            except ContinueException:
                continue
            except BreakException:
                break

        return (endIndex - index) + 1

    # for looks, with a variable name, start and end values
    elif cmd == "for":
        # get the variable name, start and end values
        varName = line[1]
        equalsIdx = line.index("=")
        toIdx = line.index("to")
        doIdx = line.index("do")

        # eval start and end vals
        startVal = int(evaluateExpression(line[equalsIdx + 1:toIdx], env))
        endVal = int(evaluateExpression(line[toIdx + 1:doIdx], env))

        # find the end of the for loop to loop it
        endIndex = index
        depth = 1
        # loop through the context to find the end of the for loop
        while endIndex < len(context) - 1:
            endIndex += 1
            if context[endIndex]:
                if context[endIndex][0] in ("if", "while", "for", "def"):
                    depth += 1
                elif context[endIndex][0] == "end":
                    depth -= 1
                    if depth == 0:
                        break

        # loop through and execute
        currentVal = startVal
        while currentVal <= endVal:
            env[varName] = currentVal
            
            i = index + 1
            try:
                while i < endIndex:
                    currLine = context[i]
                    if currLine:
                        res = runLine(currLine, context, i, env)
                        i += res if res is not None else 1
                    else:
                        i += 1
            # here is the super cool exception method again
            # super cool way to detect it
            except ContinueException:
                pass
            except BreakException:
                break
                
            currentVal += 1
            
        return (endIndex - index) + 1

    # end of blocks, like if while for and def
    elif cmd == "end":
        # ready to skip
        return 1
    # return statement raises super cool exception
    elif cmd == "return":
        retTokens = line[1:]
        # eval return val
        val = evaluateExpression(retTokens, env)
        raise ReturnException(val)
    # another awesome break exception
    elif cmd == "break":
        raise BreakException()
    # same for continue
    elif cmd == "continue":
        raise ContinueException()
    # include files inside other files
    elif cmd == "include":
        # get the current file, so its relative to the file
        # otherwise it breaks when executed in different shell dirs
        filenames = parseCallArgs(line, env)
        currentDir = env.get("__dir__", os.getcwd())

        # loop through the filenames and include them        
        for rawFilename in filenames:
            filename = str(rawFilename).strip('"\'')
            if not filename.endswith(".oxy"):
                filename += ".oxy"
                
            fullPath = os.path.join(currentDir, filename)
            
            try:
                # read file
                with open(fullPath, "r") as f:
                    fileCode = f.read()
                
                includedLines = [tokeniseLine(l) for l in fileCode.splitlines()]
                
                oldDir = env.get("__dir__")
                env["__dir__"] = os.path.dirname(os.path.abspath(fullPath))
                
                i = 0
                while i < len(includedLines):
                    l = includedLines[i]
                    if l:
                        res = runLine(l, includedLines, i, env)
                        i += res if res is not None else 1
                    else:
                        i += 1

                # restore the old dir after including
                if oldDir is not None:
                    env["__dir__"] = oldDir
                else:
                    env.pop("__dir__", None)
                    
            except FileNotFoundError:
                print(f"Error: Could not find include file '{fullPath}'")
            except Exception as e:
                print(f"Error including file '{filename}': {e}")
                
        return 1
    else:
        evaluateExpression(line, env)
        return 1

# parse val into a sting, int, float, bool or None
def parseValue(token: str, env: dict = None):
    token = token.strip()

    # check if its a string, boolean or null
    if (token.startswith('"') and token.endswith('"')) or (token.startswith("'") and token.endswith("'")):
        return token[1:-1]

    if token == "true":
        return True
    if token == "false":
        return False
    if token in ("null", "nil"):
        return None

    try:
        if "." in token:
            return float(token)
        else:
            return int(token)
    except ValueError:
        pass

    if env is not None and token in env:
        return env[token]

    return token

# get the arguments from brackets, for function calls
def getArgsFromBrackets(line: list, env: dict):
    # check if the line has brackets and is a function call
    if len(line) >= 3 and line[1] == "(" and line[-1] == ")":
        innerTokens = line[2:-1]
        args = []
        currentArg = []

        # loop through the inner tokens and split them by commas
        # also eval each arg
        for token in innerTokens:
            if token == ",":
                if currentArg:
                    args.append(evaluateExpression(currentArg, env))
                    currentArg = []
            else:
                currentArg.append(token)

        if currentArg:
            args.append(evaluateExpression(currentArg, env))

        return args
    return []

# eval expressions, takes list of tokens and env for vars and funcs
def evaluateExpression(tokens: list, env: dict):
    # check if its a function call, like input() or len() or type() or int() or str() or float() or reverse()
    if len(tokens) >= 3 and tokens[0] in ("input", "len", "type", "int", "str", "float", "reverse"):
        funcName = tokens[0]
        args = parseCallArgs(tokens, env)
        if funcName == "input":
            prompt = args[0] if args else ""
            return input(prompt)
        elif funcName == "len":
            return len(args[0]) if args else 0
        elif funcName == "type":
            val = args[0] if args else None
            t = type(val).__name__
            return {"str": "string", "int": "integer", "float": "float", "bool": "boolean"}.get(t, t)
        elif funcName == "int":
            return int(args[0]) if args else 0
        elif funcName == "str":
            return str(args[0]) if args else ""
        elif funcName == "float":
            return float(args[0]) if args else 0.0
        elif funcName == "reverse":
            val = str(args[0]) if args else ""
            return val[::-1]

    # this part is partially vibecoded slop, but it works well enough
    # check if its a list or string index access, like myList[0] or myString[1]
    resolved_tokens = []
    i = 0
    while i < len(tokens):
        if i + 2 < len(tokens) and tokens[i + 1] == "[" and tokens[i] in env:
            varName = tokens[i]
            bracket_depth = 0
            end_idx = i + 1
            while end_idx < len(tokens):
                if tokens[end_idx] == "[":
                    bracket_depth += 1
                elif tokens[end_idx] == "]":
                    bracket_depth -= 1
                    if bracket_depth == 0:
                        break
                end_idx += 1
            
            if bracket_depth == 0:
                indexTokens = tokens[i + 2:end_idx]
                idx = int(evaluateExpression(indexTokens, env))
                
                val = env[varName]
                resolved_tokens.append(repr(val[idx]))
                i = end_idx + 1
                continue
        
        resolved_tokens.append(tokens[i])
        i += 1
        
    tokens = resolved_tokens

    # check if its a func call
    if len(tokens) >= 3 and tokens[0] in env and isinstance(env[tokens[0]], dict) and env[tokens[0]]["type"] == "function":
        funcName = tokens[0]
        funcDef = env[funcName]
        
        callArgs = parseCallArgs(tokens, env)
            
        localEnv = env.copy()
        for paramName, argVal in zip(funcDef["args"], callArgs):
            localEnv[paramName] = argVal
            
        try:
            executeBlock(funcDef["context"], funcDef["startIndex"], funcDef["endIndex"], localEnv)
        except ReturnException as e:
            return e.value
        return None

    # maths evals using python eval
    # also parses tokens
    exprParts = []
    operators = {"+", "-", "*", "/", "%", "==", "!=", "<", ">", "<=", ">=", "and", "or", "not", "(", ")"}
    for token in tokens:
        if token in env:
            exprParts.append(repr(env[token]))
        elif token in operators:
            exprParts.append(token)
        else:
            val = parseValue(token, env)
            if isinstance(val, str):
                exprParts.append(repr(val))
            else:
                exprParts.append(str(val))
    
    exprStr = " ".join(exprParts)
    try:
        return eval(exprStr)
    except Exception:
        return exprStr

# run a code block, like if, while, for, def, etc
def executeBlock(context: list, startIndex: int, endIndex: int, env: dict):
    i = startIndex
    while i < endIndex:
        line = context[i]
        if line:
            result = runLine(line, context, i, env)
            if result is not None:
                i += result
            else:
                i += 1
        else:
            i += 1

# helper func to remove comments from lines
def removeComments(tokens):
    for index, token in enumerate(tokens):
        if "#" in token:
            cleanedToken = token.split("#", 1)[0]
            
            if cleanedToken == "":
                return tokens[:index]
            
            return tokens[:index] + [cleanedToken]
            
    return tokens

# helper func to tokenise a line of code into tokens
def parseCallArgs(tokens: list, env: dict):
    callArgs = []
    try:
        open_b = tokens.index("(")
        close_b = tokens.index(")")
        inner = tokens[open_b + 1:close_b]
        current = []
        for t in inner:
            if t == ",":
                if current:
                    callArgs.append(evaluateExpression(current, env))
                    current = []
            else:
                current.append(t)
        if current:
            callArgs.append(evaluateExpression(current, env))
    except ValueError:
        pass
    return callArgs

def tokeniseLine(line: str):
        # horrible regex aaaaaahhhhhhhhh
        # also claude
        pattern = r'''("[^"\\]*(?:\\.[^"\\]*)*"|'[^'\\]*(?:\\.[^'\\]*)*'|==|!=|<=|>=|[(),\[\]{}+*\/\-%<>=]|[^\s(),\[\]{}+*\/\-%<>=]+)'''
        return [t for t in re.findall(pattern, line) if t.strip()]
    