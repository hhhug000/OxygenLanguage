import argparse
import shlex
import runner

class OxygenRunner:
    def run(self, code: str):
        lines = code.splitlines()
        for i, line in enumerate(lines):
            lines[i] = shlex.split(line.strip())
        for line in lines:
            runner.runLine(line, lines)

    def repl(self):
        lines = []
        print("Oxygen REPL, Type EXIT to quit")
        while True:
            line = input(">>> ")
            if line.strip() == "EXIT":
                break
            lines.append(shlex.split(line.strip()))
            runner.runLine(lines[-1], lines)

        

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Oxygen Runner")
    parser.add_argument("file", nargs="?", type=str, help="The file with code to run")
    args = parser.parse_args()
    if args.file:
        with open(args.file, "r") as f:
                code = f.read()
                oxyrunner = OxygenRunner()
                oxyrunner.run(code)
    else:
        oxyrunner = OxygenRunner()
        oxyrunner.repl()