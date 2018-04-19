def process_input(self, key, value):
    """
    Get the movement value inputted by the user.

    For example, after pressing r to rotate, the user can input a
    rotation amount (in degrees) by pressing numbers on the keyboard
    """
    numbers = {
        'NUMPAD_0' : '0',
        'NUMPAD_1' : '1',
        'NUMPAD_2' : '2',
        'NUMPAD_3' : '3',
        'NUMPAD_4' : '4',
        'NUMPAD_5' : '5',
        'NUMPAD_6' : '6',
        'NUMPAD_7' : '7',
        'NUMPAD_8' : '8',
        'NUMPAD_9' : '9',
        'ZERO' : '0',
        'ONE' : '1',
        'TWO' : '2',
        'THREE' : '3',
        'FOUR' : '4',
        'FIVE' : '5',
        'SIX' : '6',
        'SEVEN' : '7',
        'EIGHT' : '8',
        'NINE' : '9',
        'PERIOD' : '.',
        'NUMPAD_PERIOD' : '.',
        'MINUS' : '-',
        'NUMPAD_MINUS' : '-',
        'BACK_SPACE' : '',
    }
    if key in numbers.keys() and value == 'PRESS' and not key == 'BACK_SPACE':
        self.key_val += numbers[key]

    elif key == 'BACK_SPACE' and value == 'PRESS' and len(self.key_val) > 0:
        self.key_val = self.key_val[0:-1]

    if len(self.key_val) > 1 and self.key_val.endswith('-'):
        self.key_val = '-' + self.key_val[0:-1]

    if self.key_val.count('-') > 1:
        if self.key_val.count('-') % 2 == 0:
            self.key_val = self.key_val.replace('-', '')
        else:
            self.key_val = '-' + self.key_val.replace('-', '')
