__author__ = "8030456, Schuppan, 8404886, Kraus"

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable
from abc import ABC, abstractmethod

from util import Util


class Param(ABC):
    """Abstract class for parameter"""
    @abstractmethod
    def optional() -> bool:
        """Cheking if the Parameter is optional
            True -> optional,
            False -> not optional"""
        pass

    @abstractmethod
    def name(self) -> str:
        """Returns the name of the Parameter"""
        pass

    @abstractmethod
    def constraints(self) -> str:
        """Retruns contraints for the Parameter"""
        pass

    @abstractmethod
    def parse(self, val: str) -> object:
        pass


class StringParam(Param):
    """Class to handle string parameters.
       Inherits from the Class Param"""
    def __init__(self, name: str, optional: bool = False) -> None:
        self.__name = name
        self.__optional = optional

    def optional(self) -> str:
        """Returns if the string parameter is optional"""
        return self.__optional

    def name(self) -> str:
        """Returns the name of the string parameter"""
        return self.__name

    def constraints(self):
        return "string"

    def parse(self, val: str) -> str:
        return val


class IntParam(Param):
    """Class to handle Integer parameter.
       Inherits from the class Param."""
    def __init__(
        self,
        name: str,
        optional: bool = False,
        min: int | None = None,
        max: int | None = None,
    ) -> None:
        self.__name = name
        self.__optional = optional
        self.__min = min
        self.__max = max

    def optional(self) -> str:
        """Returns if the Integer parameter is optional"""
        return self.__optional

    def name(self) -> str:
        """Returns the name of the Integer parameter
           True -> is optional
           False -> is not optional"""
        return self.__name

    def constraints(self) -> str:
        """Returns min and/or max values of the Integer"""
        res = "int"
        if self.__min is not None:
            res += f" from {self.__min}"
        if self.__max is not None:
            res += f" to {self.__max}"
        return res

    def parse(self, val: str) -> float:
        """Check the input with using the constraints
           Returns the correct number as float or
           Returns a Error to tell the mistake"""
        i = 0
        try:
            i = int(val)
        except:
            raise ValueError("expected integer")
        if self.__min is not None:
            if i < self.__min:
                raise ValueError(
                    f"expected number to be at least {self.__min}"
                )
        if self.__max is not None:
            if i > self.__max:
                raise ValueError(f"expected number to be at most {self.__max}")
        return i


@dataclass
class Command:
    """Command is a command that can be executed in the shell.
    The signature for the run callback is inteded as follows:
    def my_cmd(self, params: list[object]) -> None:"""

    name: str
    description: str
    params: list[Param]
    run: Callable[[object, list[object]], None]


class Shell:
    """Shell is a generalized interactive shell which can
    execute commands via callbacks. Commands can be registered
    using add_command."""

    def __init__(self) -> None:
        self.__prompt_elems: list[str] = []
        self.__commands: dict[str, Command] = {}

    def add_command(self, cmd: Command) -> None:
        """Adds a new command to the shell. Raises an
        an exception if the command was invalid."""
        seen_optional_param = False
        for param in cmd.params:
            if seen_optional_param and not param.optional():
                raise ValueError("only the last parameters may be optional")
            if param.optional():
                seen_optional_param = True

        self.__commands[cmd.name] = cmd

    def help(self) -> str:
        """Print a nicely formatted help page listing
        commands and their parameters and descriptions."""

        rows = [
            ["exit", "exit the shell"],
            ["help", "show this page"],
        ]

        for cmd in self.__commands.values():
            words = [cmd.name]
            for p in cmd.params:
                word = f"{p.name()}: {p.constraints()}"
                if p.optional():
                    word = f"[{word}]"
                else:
                    word = f"<{word}>"
                words.append(word)
            rows.append([" ".join(words), cmd.description])

        for row in rows:
            row[0] = "  " + row[0]

        prolog = [
            'Command format: "command <required_parameter> \
[optional_parameter]"',
            "Commands:",
        ]

        return "\n".join(prolog) + "\n" + Util.column_align(rows, sep=" - ")

    def set_prompt_prefix(self, elems: list[str]) -> None:
        """Sets the prefix words which will be printed
        before each prompt, separated by spaces."""
        self.__prompt_elems = elems

    def run(self, init_prompt: str) -> None:
        """Runs the main shell loop."""
        print(init_prompt)
        print('Type "help" for a list of commands.')
        while True:
            try:
                prompt = " ".join(self.__prompt_elems + [">> "])
                args = input(prompt).split()
                if len(args) == 0:
                    continue
                if args[0] == "help":
                    print(self.help())
                elif args[0] == "exit" or args[0] == "quit":
                    print("Exiting.")
                    break
                elif args[0] in self.__commands:
                    cmd = self.__commands[args[0]]
                    num_params = len(args) - 1
                    min_params = sum(
                        0 if p.optional else 1 for p in cmd.params
                    )
                    max_params = len(cmd.params)
                    if num_params < min_params:
                        plural = "" if min_params == 1 else "s"
                        print(f"{args[0]} expects at least \
{min_params} parameter{plural}.")
                        continue
                    if num_params > max_params:
                        if max_params == 0:
                            print(
                                f"{args[0]} expects no \
parameters."
                            )
                        else:
                            print(
                                f"{args[0]} expects at most \
{max_params} parameters."
                            )
                        continue
                    params_not_ok = False
                    params = []
                    for i, param in enumerate(cmd.params):
                        if i + 1 >= len(args):
                            # Optional param wasn't specified.
                            params.append(None)
                            continue
                        try:
                            params.append(param.parse(args[i + 1]))
                        except Exception as e:
                            print(
                                f"Error: {cmd.name}: \
{param.name}: {e}."
                            )
                            params_not_ok = True
                            break
                    if params_not_ok:
                        continue
                    cmd.run(self, params)
                else:
                    print(f'Unknwon command "{args[0]}"!')
                    print('Type "help" for a list of commands.')
                print()
            except KeyboardInterrupt:
                print()
                print('Type "exit" or "quit", or ctrl+d to quit.')
                continue
            except EOFError:
                print()
                print("Exiting.")
                break
