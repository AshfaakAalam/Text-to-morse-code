import time
from time import sleep

UNIT = 0.2  # base time unit
string = input("Enter text: ").lower()

morse_codes = {
    "a": ".-",
    "b": "-...",
    "c": "-.-.",
    "d": "-..",
    "e": ".",
    "f": "..-.",
    "g": "--.",
    "h": "....",
    "i": "..",
    "j": ".---",
    "k": "-.-",
    "l": ".-..",
    "m": "--",
    "n": "-.",
    "o": "---",
    "p": ".--.",
    "q": "--.-",
    "r": ".-.",
    "s": "...",
    "t": "-",
    "u": "..-",
    "v": "...-",
    "w": ".--",
    "x": "-..-",
    "y": "-.--",
    "z": "--..",
    " ": " "
}

for char in string:
    code = morse_codes.get(char)

    if code is None:
        continue

    if char == " ":
        print("   ", end="")
        time.sleep(UNIT*7)
        continue

    for symbol in code:
        if symbol == ".":
            print(".", end="", flush=True)

        elif symbol == "-":
            print("-", end="", flush=True)
        sleep(UNIT)

    print(" ", end="")
    time.sleep(UNIT*2)

print()