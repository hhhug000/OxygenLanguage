import argparse
import os
import re
import runner

class OxygenRunner:
    # Main entrypoint, takes in code string and runs it
    # Env is the variable and function scope, also for dir and includes
    def run(self, code: str, env: dict = {}):
        lines = code.splitlines()
        # Tokenise code so its easy to run
        for i, line in enumerate(lines):
            lines[i] = runner.tokeniseLine(line.strip())

        i = 0
        while i < len(lines):
            line = lines[i]
            # run the line and return the number of lines to skip
            # otherwise functions and loops get broken
            result = runner.runLine(line, lines, i, env)
            if result is not None:
                i += result
            else:
                i += 1

    def repl(self):
        lines = []
        buffer = []
        # Figure out if its in code blocks
        blockDepth = 0
        env = {}
        print("Oxygen REPL, Type EXIT to quit")
        while True:
            if blockDepth > 0:
                # use ... for code blocks
                prompt = "... "
            else:
                prompt = ">>> "
            line = input(prompt)

            stripped = line.strip()
            if blockDepth == 0 and stripped == "EXIT":
                break
            if not stripped:
                continue

            tokens = runner.tokeniseLine(stripped)
            buffer.append(tokens)

            if tokens and tokens[0] in ("def", "if", "while", "for"):
                blockDepth += 1
            elif tokens and tokens[0] == "end":
                blockDepth -= 1

            # Force it to be 0 if it goes negative
            # otherwise a weird bug sometimes happens
            if blockDepth <= 0:
                blockDepth = 0

                i = 0
                while i < len(buffer):
                    line = buffer[i]
                    result = runner.runLine(buffer[i], buffer, i, env)
                    if result is not None:
                        i += result
                    else:
                        i += 1

                lines.extend(buffer)
                buffer = []

        

if __name__ == "__main__":
    # make it support arguments
    parser = argparse.ArgumentParser(description="Oxygen Runner")
    parser.add_argument("file", nargs="?", type=str, help="The file with code to run")
    args = parser.parse_args()
    oxyrunner = OxygenRunner()
    # if code file is given then run it, otherwise repl
    if args.file:
        scriptPath = args.file
        with open(args.file, "r") as f:
                code = f.read()
                # dir so includes work, for relative paths
                env = {
                    "__dir__": os.path.dirname(os.path.abspath(scriptPath))
                }
                oxyrunner.run(code, env = env)
    else:
        oxyrunner.repl()