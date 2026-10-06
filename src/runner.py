class ReturnException(Exception):
    def __init__(self, value):
        self.value = value

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
        try:
            thenIndex = line.index("then")
            condTokens = line[1:thenIndex]
        except ValueError:
            condTokens = line[1:]

        conditionMet = bool(evaluateExpression(condTokens, env))

        endIndex = index
        depth = 1
        while endIndex < len(context):
            endIndex += 1
            if context[endIndex]:
                if context[endIndex][0] in ("if", "while", "def"):
                    depth += 1
                elif context[endIndex][0] == "end":
                    depth -= 1
                    if depth == 0:
                        break
        if conditionMet:
            executeBlock(context, index + 1, endIndex, env)
        return (endIndex - index) + 1
    
    elif cmd == "while":
        try:
            doIndex = line.index("do")
            condTokens = line[1:doIndex]
        except ValueError:
            condTokens = line[1:]
            
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
                        
        while bool(evaluateExpression(condTokens, env)):
            executeBlock(context, index + 1, endIndex, env)
        return (endIndex - index) + 1
    
    elif cmd == "end":
        return 1
    elif cmd == "return":
        retTokens = line[1:]
        val = evaluateExpression(retTokens, env)
        raise ReturnException(val)
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
    if len(tokens) >= 3 and tokens[0] in env and isinstance(env[tokens[0]], dict) and env[tokens[0]]["type"] == "function":
        funcName = tokens[0]
        funcDef = env[funcName]
        
        callArgs = []
        try:
            openB = tokens.index("(")
            closeB = tokens.index(")")
            inner = tokens[openB + 1:closeB]
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