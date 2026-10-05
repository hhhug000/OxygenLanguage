import argparse
import re
import runner

class OxygenRunner:
    def tokeniseLine(self, line: str):
        pattern = r'''("[^"\\]*(?:\\.[^"\\]*)*"|'[^'\\]*(?:\\.[^'\\]*)*'|[(),\[\]{}]|[^\s(),\[\]{}]+)'''
        return [t for t in re.findall(pattern, line) if t.strip()]
    
    def run(self, code: str):
        lines = code.splitlines()
        for i, line in enumerate(lines):
            lines[i] = self.tokeniseLine(line.strip())
        
        i = 0
        while i < len(lines):
            line = lines[i]
            result = runner.runLine(line, lines, i)
            if result is not None:
                i += result
            else:
                i += 1

    def repl(self):
        lines = []
        buffer = []
        blockDepth = 0
        print("Oxygen REPL, Type EXIT to quit")
        while True:
            if blockDepth > 0:
                prompt = "... "
            else:
                prompt = ">>> "
            line = input(prompt)

            stripped = line.strip()
            if blockDepth == 0 and stripped == "EXIT":
                break
            if not stripped:
                continue

            tokens = self.tokeniseLine(stripped)
            buffer.append(tokens)

            if tokens and tokens[0] in ("def", "if", "while", "for"):
                blockDepth += 1
            elif tokens and tokens[0] == "end":
                blockDepth -= 1

            if blockDepth <= 0:
                blockDepth = 0

                i = 0
                while i < len(buffer):
                    line = buffer[i]
                    result = runner.runLine(buffer[i], buffer, i)
                    if result is not None:
                        i += result
                    else:
                        i += 1

                lines.extend(buffer)
                buffer = []

        

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Oxygen Runner")
    parser.add_argument("file", nargs="?", type=str, help="The file with code to run")
    args = parser.parse_args()
    oxyrunner = OxygenRunner()
    if args.file:
        with open(args.file, "r") as f:
                code = f.read()
                oxyrunner.run(code)
    else:
        oxyrunner.repl()