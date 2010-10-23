from cx_Freeze import setup, Executable

setup(
        name = "hello",
        version = "0.1",
        description = "the typical 'Hello, world!' script",
        executables = [Executable("entris.py")])
