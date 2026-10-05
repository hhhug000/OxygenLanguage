import argparse

class OxygenRunner:
    def run(self, code: str):
        lines = code.splitlines()
        for i, line in enumerate(lines):
            lines[i] = line.strip().split(" ")
        for line in lines:
            print(f"Executing line: {line}")

    def repl(self):
        lines = []
        print("Oxygen REPL, Type EXIT to quit")
        while True:
            line = input(">>> ")
            if line.strip() == "EXIT":
                break
            lines.append(line.strip().split(" "))
            print(f"Executing line: {lines[-1]}")

        

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Oxygen Runner")
    parser.add_argument("file", nargs="?", type=str, help="The file with code to run")
    args = parser.parse_args()
    if args.file:
        with open(args.file, "r") as f:
                code = f.read()
                runner = OxygenRunner()
                runner.run(code)
    else:
        runner = OxygenRunner()
        runner.repl()