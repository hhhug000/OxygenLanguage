import os
import re

class ReturnException(Exception):
    def __init__(self, value):
        self.value = value

class BreakException(Exception):
    pass

class ContinueException(Exception):
    pass

def runLine(line, context, index, env):
    if not line:
        return 1
    
    cmd = line[0]

    line = removeComments(line)

    if len(line) >= 3 and line[1] == "=":
        varName = line[0]
        rhsTokens = line[2:]
        env[varName] = evaluateExpression(rhsTokens, env)
        return 1

    if cmd == "print":
        args = getArgsFromBrackets(line, env)
        print(*args)
        return 1
    elif cmd == "def":
        funcName = line[1]

        argTokens = []
        try:
            openBracket = line.index("(")
            closeBracket = line.index(")")
            argTokens = line[openBracket + 1:closeBracket]
        except ValueError:
            pass

        argNames = [token for token in argTokens if token != ","]

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

        env[funcName] = {
            "type": "function",
            "args": argNames,
            "startIndex": index + 1,
            "endIndex": endIndex,
            "context": context
        }

        return (endIndex - index) + 1

    elif cmd == "if":
        branches = []
        
        try:
            thenIndex = line.index("then")
            currentCond = line[1:thenIndex]
        except ValueError:
            currentCond = line[1:]
            
        branchStart = index + 1
        
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
    
    elif cmd == "while":
        condTokens = line[1 : line.index("do")] if "do" in line else line[1:]
        
        endIndex = index
        depth = 1
        while endIndex < len(context) - 1:
            endIndex += 1
            if context[endIndex]:
                if context[endIndex][0] in ("if", "while", "for", "def"):
                    depth += 1
                elif context[endIndex][0] == "end":
                    depth -= 1
                    if depth == 0:
                        break

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
            except ContinueException:
                continue
            except BreakException:
                break

        return (endIndex - index) + 1
    elif cmd == "for":
        varName = line[1]
        equalsIdx = line.index("=")
        toIdx = line.index("to")
        doIdx = line.index("do")
        
        startVal = int(evaluateExpression(line[equalsIdx + 1:toIdx], env))
        endVal = int(evaluateExpression(line[toIdx + 1:doIdx], env))
        
        endIndex = index
        depth = 1
        while endIndex < len(context) - 1:
            endIndex += 1
            if context[endIndex]:
                if context[endIndex][0] in ("if", "while", "for", "def"):
                    depth += 1
                elif context[endIndex][0] == "end":
                    depth -= 1
                    if depth == 0:
                        break
                      
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
            except ContinueException:
                pass
            except BreakException:
                break
                
            currentVal += 1
            
        return (endIndex - index) + 1
    
    elif cmd == "end":
        return 1
    elif cmd == "return":
        retTokens = line[1:]
        val = evaluateExpression(retTokens, env)
        raise ReturnException(val)
    elif cmd == "break":
        raise BreakException()
    elif cmd == "continue":
        raise ContinueException()
    elif cmd == "include":
        filenames = parseCallArgs(line, env)
        currentDir = env.get("__dir__", os.getcwd())
        
        for rawFilename in filenames:
            filename = str(rawFilename).strip('"\'')
            if not filename.endswith(".oxy"):
                filename += ".oxy"
                
            fullPath = os.path.join(currentDir, filename)
            
            try:
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

def parseValue(token: str, env: dict = None):
    token = token.strip()

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

def getArgsFromBrackets(line: list, env: dict):
    if len(line) >= 3 and line[1] == "(" and line[-1] == ")":
        innerTokens = line[2:-1]
        args = []
        currentArg = []

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

def evaluateExpression(tokens: list, env: dict):
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

def removeComments(tokens):
    for index, token in enumerate(tokens):
        if "#" in token:
            cleanedToken = token.split("#", 1)[0]
            
            if cleanedToken == "":
                return tokens[:index]
            
            return tokens[:index] + [cleanedToken]
            
    return tokens

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
        pattern = r'''("[^"\\]*(?:\\.[^"\\]*)*"|'[^'\\]*(?:\\.[^'\\]*)*'|==|!=|<=|>=|[(),\[\]{}+*\/\-%<>=]|[^\s(),\[\]{}+*\/\-%<>=]+)'''
        return [t for t in re.findall(pattern, line) if t.strip()]
    