import random
import os
import string
from sys import platform
from enum import Enum

from colorama import Fore, init, deinit


class Gem(Enum):
    red = 1
    magenta = 2
    yellow = 3
    green = 4
    blue = 5


_gem_list = list(Gem)


class NotBejeweled:
    def __init__(self, x, y):
        self.exit = False
        self.x = x
        self.y = y
        self.score = 0
        self.board = []
        self.msg = ''

        # generate board
        for i in range(x):
            row = []

            # todo: avoid generating automatic matches :)
            for x in range(y):
                row.append(random.choice(_gem_list))
            self.board.append(row)

        # misc pretty things
        self.header_spacing = ' ' * ((3 * (x+1)) - len('Not Bejeweled'))

    def play(self):
        # todo: optimize with board introspection
        while self.match_gems():
            self.drop_gems()

        self.score = 0
        while not self.exit:
            self.print_board()
            try:
                cell_1, cell_2 = self.user_move()
            except TypeError:
                print('\nERROR:', self.msg)
                self.msg = ''
                input('Press enter to continue...')
                continue

            matches = self.match_gems(*cell_1)
            matches += self.match_gems(*cell_2)
            if matches:
                self.update_score(matches)
                self.print_board()
                input('Press enter to continue...')
            else:
                self.swap_cells(*(cell_1 + cell_2))
                print("\nERROR: Swap didn't change anything!")
                input('Press enter to continue...')

            while True:
                self.drop_gems()
                if self.update_score(self.match_gems()) == 0:
                    break
                    # todo: self.check_lost()

    def print_board(self):
        if platform == 'win32':
            os.system('cls')
        else:
            os.system('clear')
        print('Not Bejeweled', self.header_spacing, 'Score:', self.score, end='\n\n')
        print('   ', '   '.join(map(str, range(1, self.x + 1))))
        print('   ', '-' * (4 * self.x - 1), sep='')
        for i, row in enumerate(self.board):
            row_letter = string.ascii_uppercase[i]
            print(row_letter, '|', end='')
            for cell in row:
                if cell is not None:
                    # print gem
                    gem_color = getattr(Fore, cell.name.upper())
                    print(' {}*{} |'.format(gem_color, Fore.RESET), end='')
                else:
                    print('   |', end='')
            print('', row_letter)

        print('   ', '-' * (4 * self.x - 1), sep='')
        print('   ', '   '.join(map(str, range(1, self.x + 1))), end='\n\n')

    def _get_move(self, cell_name):
        cell = input('{} cell to switch: '.format(cell_name)).strip()
        row, col = cell[0], cell[1:]
        col = int(col) - 1
        row = string.ascii_uppercase[:self.x].find(row.upper())
        if row < 0 or col < 0:
            raise ValueError

        return row, col

    def swap_cells(self, x1, x2, y1, y2):
        cell_2_tmp = self.board[x2][y2]
        self.board[x2][y2] = self.board[x1][y1]
        self.board[x1][y1] = cell_2_tmp

    def user_move(self):
        try:
            x1, y1 = self._get_move('First')
            if x1 >= self.x or y1 >= self.y:
                raise ValueError()
        except (KeyError, ValueError, IndexError):
            self.msg = 'Invalid first cell coordinate!'
            return

        try:
            x2, y2 = self._get_move('Second')
            if x2 >= self.x or y2 >= self.y:
                raise ValueError()
        except (KeyError, ValueError, IndexError):
            self.msg = 'Invalid second cell coordinate!'
            return

        if x1 == x2 and y1 == y2:
            self.msg = 'Specify two different cells!'
            return

        if abs(x1 - x2) > 1 or abs(y1 - y2) > 1:
            self.msg = 'Specify two adjacent cells!'
            return

        # swap cells 1 and 2
        self.swap_cells(x1, x2, y1, y2)

        # return move coordinates for further use
        return (x1, y1), (x2, y2)

    def drop_gems(self):
        # drop existing gems
        cols_to_fill = set()
        for x, row in reversed(list(enumerate(self.board))):
            for y, cell in enumerate(row):
                if self.board[x][y] is None:
                    cols_to_fill.add(y)
                    # compute offset to first non-empty cell
                    x_offset = None
                    for i in range(x, -1, -1):
                        if self.board[i][y] is not None:
                            x_offset = x - i
                            break

                    # if there's anything to pull down...
                    if x_offset is not None:
                        for i in range(x, x - x_offset, -1):
                            # todo: prevent negative indexing in a real way lol
                            if i - x_offset < 0:
                                break
                            self.board[i][y] = self.board[i - x_offset][y]
                            self.board[i - x_offset][y] = None

        # drop new gems
        for y in cols_to_fill:
            for x, row in enumerate(self.board):
                if self.board[x][y] is None:
                    self.board[x][y] = random.choice(_gem_list)

    def match_gems(self, x=None, y=None):
        # check if we have a row or column of 3+ gems
        removed_cells = []
        if x is not None and y is not None:
            cells = self._get_matching_gems(x, y)
            if cells:
                self._remove_cells(cells)

            cells += self.match_gems()
            return cells

        # check to see if there are /any/ gems that match
        for x, row in enumerate(self.board):
            for y, cell in enumerate(row):
                if not (x, y) in removed_cells:
                    # check directions
                    removed_cells += self._get_matching_gems(x, y)

        # call it again to see if we've got a chain
        if removed_cells:
            self._remove_cells(removed_cells)
            removed_cells += self.match_gems()

        return removed_cells

    def _get_matching_gems(self, center_x, center_y):
        # get directions to search
        up, down, left, right = False, False, False, False
        # edge casesss
        if center_x == 0:
            # top left
            if center_y == 0:
                right = True
                down = True
            # top right
            elif center_y == self.y - 1:
                right = True
                up = True
            # bottom
            else:
                right = True
                up = True
                down = True
        elif center_x == self.x - 1:
            # bottom left
            if center_y == 0:
                up = True
                right = True
            # bottom right
            elif center_y == self.y - 1:
                up = True
                left = True
            # bottom
            else:
                up = True
                left = True
                right = True
        else:
            # left
            if center_y == 0:
                up = True
                right = True
                down = True
            # right
            elif center_y == self.y - 1:
                up = True
                left = True
                down = True
            # anywhere else
            else:
                up, down, left, right = True, True, True, True

        center_cell = self.board[center_x][center_y]
        horizontal_matches = [(center_x, center_y)]
        if up:
            for x in range(center_x - 1, -1, -1):
                cell = self.board[x][center_y]
                if cell is not None and cell == center_cell:
                    horizontal_matches.append((x, center_y))
                else:
                    break

        if down:
            for x in range(center_x + 1, self.x, 1):
                cell = self.board[x][center_y]
                if cell is not None and cell == center_cell:
                    horizontal_matches.append((x, center_y))
                else:
                    break

        vertical_matches = [(center_x, center_y)]
        if left:
            for y in range(center_y - 1, -1, -1):
                cell = self.board[center_x][y]
                if cell is not None and cell == center_cell:
                    vertical_matches.append((center_x, y))
                else:
                    break
        if right:
            for y in range(center_y + 1, self.y, 1):
                cell = self.board[center_x][y]
                if cell is not None and cell == center_cell:
                    vertical_matches.append((center_x, y))
                else:
                    break

        matches = [(center_x, center_y)]
        if len(vertical_matches) >= 3:
            matches.extend(vertical_matches[1:])
        if len(horizontal_matches) >= 3:
            matches.extend(horizontal_matches[1:])
        if len(matches) == 1:
            return []
        else:
            return matches

    def _remove_cells(self, cells):
        assert (len(cells) > 1)
        for x, y in cells:
            self.board[x][y] = None

            # drop cells down

    def update_score(self, matches):
        num_gems = len(matches)
        delta = 0
        if num_gems < 4:
            delta = num_gems
        elif num_gems < 6:
            delta = 3 + 2 * (num_gems - 3)
        elif num_gems >= 6:
            delta = 3 + 2 * (num_gems - 3) + 3 * (num_gems - 5)
        self.score += delta
        return delta


def main():
    init()
    NotBejeweled(8, 8).play()
    deinit()


if __name__ == '__main__':
    main()