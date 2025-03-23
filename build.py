import argparse
import subprocess
import os
import shutil

class Builder:
    """
    构建python包的自动化工具
    """
    def __init__(self, command_file: str) -> None:
        self.command_file = command_file
        self.commands = []
        self.read_commands()

    def clean_dist(self) -> None:
        # 删除dist文件夹
        if os.path.exists('dist'):
            print("Removing dist folder")
            shutil.rmtree('dist')

    def remove_pycache(self, dir: str) -> None:
        # 查找指定的文件夹下和子文件夹下的所有__pycache__文件夹, 并删除
        for root, dirs, files in os.walk(dir):
            for name in dirs:
                if name == '__pycache__':
                    print(f"Removing __pycache__ folder: {os.path.join(root, name)}")
                    shutil.rmtree(os.path.join(root, name))

    def read_commands(self) -> None:
        try:
            with open(self.command_file, 'r') as f:
                for line in f:
                    self.commands.append(line.strip())
        except OSError as e:
            print(f"Error reading command file: {e}")
            exit(1)

    def build(self) -> None:
        self.clean_dist()
        for command in self.commands:
            print(f"Executing command: {command}")
            try:
                result = subprocess.run(command, shell=True, check=True)
                if result.returncode!= 0:
                    print(f"Command failed: {command}. Error: {result.stderr}")
                    exit(result.returncode)
            except subprocess.CalledProcessError as e:
                print(f"Command failed: {command}. Error: {e}")
                exit(e.returncode)

    def __del__(self) -> None:
        self.remove_pycache('FuXLogger')

def main():
    parser = argparse.ArgumentParser(description="Simple build script")
    parser.add_argument("command_file", help="File containing commands to execute")
    args = parser.parse_args()

    builder = Builder(args.command_file)
    builder.build()
    del builder # 调用__del__方法删除__pycache__文件夹

if __name__ == '__main__':
    main()