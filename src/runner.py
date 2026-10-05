def runLine(line, context, index):
    cmd = line[0]

    if cmd == "print":
        print(" ".join(line[1:]))
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