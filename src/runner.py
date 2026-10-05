def runLine(line, context, index):
    cmd = line[0]

    if cmd == "print":
        args = getArgsFromBrackets(line)
        print(args)
        return 1
    elif cmd == "def":
        print(f"Defining function: {line[1]}")
        endIndex = index
        while endIndex < len(context):
            if context[endIndex][0] == "end" and context[endIndex]:
                break
            endIndex += 1
        print(f"New function from lines {index} to {endIndex}")
        return (endIndex-index) + 1
    elif cmd == "end":
        return 1
    else:
        print(f"Eval {line}")
        return 1

def parseValue(token: str):
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

    return token

def getArgsFromBrackets(line: list):
    if len(line) < 3 or line[1] == "(" and line[-1] == ")":
        innerTokens = line[2:-1]
        args = []
        currentArg = []

        for token in innerTokens:
            if token == ",":
                if currentArg:
                    args.append(parseValue(" ".join(currentArg)))
                    currentArg = []
            else:
                currentArg.append(token)

        if currentArg:
            args.append(parseValue(" ".join(currentArg)))

        return args
    return []