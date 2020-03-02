from datetime import datetime as dt
import copy
import sys
import argparse

start_time = dt.now()

DEBUG = False
BASE_ZERO = 0

#########################################
#BASIC
#########################################
parser = argparse.ArgumentParser(description='Simple puzzle solver named Npuzzle');

parser.add_argument('-f', '--file', dest='file',
                    help='clarify place of the file with puzzle', required=True)

#########################################
#BONUSES
#########################################
parser.add_argument('--visual', dest='visual', action='store_true', default=False,
                help='start to visualise algorithm logic', required=False)

parser.add_argument('-m', '--metric', dest='metric', type=int, default=1, choices=range(1, 7),
                help='what metric you want? 1 - Manhattan, 2 - Euclidean, 3 - Chebyshev, 4 - Minkowski, 5 - Hamming, 6 - Canberra', required=False)

parser.add_argument('-s', '--search', dest='search', type=int, default=1, choices=range(1, 4),
                help='what search you want? : 1 - a* , 2 - greedy, 3 - uniform-cost; ', required=False)

parser.add_argument('--basic', dest='basic', action='store_true', default=False,
                help='basic number position instead of snail', required=False)

parser.add_argument('--error', dest='error', action='store_true', default=False,
                help='check errors in the input game map', required=False)

parser.add_argument('--debug', dest='debug', action='store_true', default=False,
                help='enable debug logs', required=False)



class Reader:
	@staticmethod
	def errors_check_read(filename):
	    fo = open(filename, "r+")
	    firstline = ""
	    # Scip comments lines (ex: #comments comments)
	    while firstline == "":
	        firstline = fo.readline().split("#")[0].strip()
	    # First line should be just one digit(ex: 4  #comment)
	    if firstline.isdigit() == False or len(firstline.strip()) > 2:
	        print("Error. in first line - should be int 1 or int > 2: \"" + firstline + "\"")
	        return 0, None
	    puzzle_size = int (firstline[0])
	    if puzzle_size <= 0:
	        print ("Error. Size of puzzle is incorrect - should be int with value > 0")
	        return 0, None
	    puzzle = [[0] * puzzle_size for i in range(puzzle_size)]
	    used_nums = []
	    for i in range(puzzle_size):
	        # Scip comments lines.
	        line = ""
	        while line == "":
	            line = fo.readline()
	            if line == "":
	                print("Error not enought info. Incomplite puzzle")
	                return 0, None
	            # Remove spaces and comment from needed line
	            line = line.split("#")[0].strip()
	        if line:
	            # Read puzzle
	            puzzle[i] = line.split()
	            # Check number of cells in our puzzle, should be as puzzle_size
	            if len(puzzle[i]) != puzzle_size:
	                print ("Error. Incorrect number of cells in line: \"" + line + "\". Should be: " + str(puzzle_size) + " instead of " + str(len(puzzle[i])))
	                return 0, None
	
	            # Check that all cells are digits.
	            for j in range(puzzle_size):
	                if puzzle[i][j].isdigit() == False:
	                    print ("Error. All cells should contain just digits: \"" + puzzle[i][j] + "\"")
	                    return 0, None
	                used_nums.append(int(puzzle[i][j]))
	                puzzle[i][j] = int (puzzle[i][j])
	
	    # Check that we have all numbers from [0 to puzzle_size]
	    used_nums.sort()  
	    for i in range(len(used_nums)):
	        if i != len(used_nums) - 1 and used_nums[i + 1] - used_nums[i] != 1:
	            print ("Error. You have used incorrect numbers in the puzzle map. Dummy!")
	            return 0, None
	        if puzzle_size == 1:
	        	if used_nums[0] != 1:
	        		Printer.logger('term', 'Error. board size is 1, and your digit isn\'t 1. Dummy!')
	        		return 0, None
	        if used_nums[0] != 0 and puzzle_size != 1:
	            print ("Error. Incorrect numbers. Always should contain \'0\'.")
	            return 0, None
	    return puzzle_size, puzzle

	@staticmethod
	def simple_read(filename):
	    fo = open(filename, "r+")
	    firstline = ""
	    # Scip comments lines (ex: #comments comments)
	    while firstline == "":
	        firstline = fo.readline().split("#")[0].strip()
	    puzzle_size = int (firstline[0])
	    puzzle = [[0] * puzzle_size for i in range(puzzle_size)]
	    used_nums = []
	    for i in range(puzzle_size):
	        # Scip comments lines.
	        line = ""
	        while line == "":
	            line = fo.readline()
	            line = line.split("#")[0].strip()
	        if line:
	            puzzle[i] = line.split()
	            for j in range(puzzle_size):
	                used_nums.append(int(puzzle[i][j]))
	                puzzle[i][j] = int (puzzle[i][j])
	    if (puzzle_size > 1):
	    	print ("Read puzzle: {}".format(puzzle))
	    return puzzle_size, puzzle

#=======================================================================================
#Class Solvable decide if puzzle is solvable or not

class Solvable:

	@staticmethod
	def find_coordinates_of_the_given_digit(digit, full_puzzle_map):
		for y, ryadok in enumerate(full_puzzle_map):
			for x, kolonka in enumerate(ryadok):
				if full_puzzle_map[y][x] == digit:
					return y, x
				else:
					continue

	@staticmethod
	def find_zero_cell(puzzle):
		return Solvable.find_coordinates_of_the_given_digit(BASE_ZERO , puzzle)
	
	@staticmethod
	def can_solve(input_map, good_map):
	    #check position of the '0' on the good map and input map
	    #step1
		perfect_ryadok, good_col = Solvable.find_zero_cell (good_map)
		row, col = Solvable.find_zero_cell (input_map)
	
	    #check distance beetwen them with x and y
		dist = abs(good_col - col) + abs(perfect_ryadok - row)
	    #inversion_dict = get_inversion_dict(good_state)

		#manipulation with input map
		#check with formule from wikipedia is solvable or not
		#set lists with next digits
		Printer.logger('debug', 'Checking if puzzle is solvable')
		utility_dictionary = dict()
	
		map_len = len(input_map[0])
	
	    #print ("input map", len(input_map))
		for father_y in range(len(input_map)):
			for father_x in range(map_len):
				father_digit = input_map[father_y][father_x]
				utility_dictionary[father_digit] = list()
				for row in range(map_len):
					if row >= father_y:
						for col in range(map_len):
							if (col >= father_x or (col < father_x and row != father_y)) and father_digit != input_map[row][col]:
								utility_dictionary[father_digit].append(input_map[row][col])
	
		#Example
		# Received puzzle:
		# [6, 7, 5]
		# [3, 0, 1]
		# [8, 4, 2]
		# That will be inside inversion dict 'key' - is digit, 'value' - list with digits after 'key' from received puzzle
		#{
		#6: [7, 5, 3, 0, 1, 8, 4, 2], 
		#7: [5, 3, 0, 1, 8, 4, 2],
		#5: [3, 0, 1, 8, 4, 2],
		#3: [0, 1, 8, 4, 2],
		#0: [1, 8, 4, 2],
		#1: [8, 4, 2],
		#8: [4, 2],
		#4: [2],
		#2: []
		#}
		#That will be output of the inversion dictionary to next calculation with formula from wiki
	
		Printer.logger('debug', f'utility dictionary (childrens of each digit from map) {utility_dictionary}')
		inversion_dict = utility_dictionary
		puzzle = input_map
		count_inverse = 0
		for check_row in range(len(puzzle)):
			for check_col in range(len(puzzle[0])):
				to_check = puzzle[check_row][check_col]
				for row in range(len(puzzle)):
					if row >= check_row:
						for col in range(len(puzzle[0])):
							if (col >= check_col or (col < check_col and row != check_row)) and to_check in inversion_dict[puzzle[row][col]]:
								count_inverse += 1

		count_solvability = 0
		for father_y in range(len(input_map)):
			for father_x in range(map_len):
				father_digit = input_map[father_y][father_x]
				for row in range(map_len):
					if row >= father_y:
						for col in range(map_len):
							if (col >= father_x or (col < father_x and row != father_y)) and father_digit in utility_dictionary[input_map[row][col]]:
								count_solvability += 1

		Printer.logger('debug', f"counted solavbility, value = {count_solvability}. Checking if puzzle is solvable")
		if (count_solvability % 2 == 0 and dist % 2 == 0) or (count_solvability % 2 != 0 and dist % 2 != 0):
			Printer.logger('debug', "Puzzle is solvable")
			return True
		Printer.logger('debug', "Puzzle is not solvable")
		return False


#=======================================================================================
#Class Print used for displaying results, print puzzle, any debug information etc

class Printer:

	@staticmethod
	def print_puzzle(puzzle, puzzle_size):
		for i in range(puzzle_size):
			Printer.logger('term', puzzle[i]) 

	@staticmethod
	def debug_print_puzzle(puzzle, puzzle_size):
		if (DEBUG):
			for i in range(puzzle_size):
				Printer.logger('debug', puzzle[i])

	def display_puzzle(self, tab, padding, puzzle_size):
	    pass

	@staticmethod
	def step_visualization(final_path):
		for move in final_path:
			for row in move:
				Printer.logger('term' , ' '.join(map(str, row)))
		Printer.logger('term', ' ')

	@staticmethod
	def display_results(moves_to_finish, complexTime, complexSize, visualization):
	    if visualization == True:
	        Printer.step_visualization(moves_to_finish)
	    Printer.logger('term', f"complex time: {str(complexTime)}")
	    Printer.logger('term', f"complex size: {str(complexSize)}")
	    Printer.logger('term', f"how many steps required: {str(len(moves_to_finish) - 1)}")
	    Printer.logger('term', f"full program time: {str(dt.now() - start_time)}")

	@staticmethod
	def logger(module, str):
		#ToDo: done. parse here two type of logs: 
		#1. console logs that will be available for users in terminal
		#2. debug logs that you will see with special flag
		if (module == 'term'):
			print(str)
		if (module == 'debug'):
			if (DEBUG):
				print (f'debug: {str}')

#=======================================================================================
#Class Generator using for generation of the goal puzzle, reference puzzle board (etalonnaya model koroche)

class Generator:
	#old function used to provide final board state with limitation: accept only from 2x2 to 5x5.
	#keep going in that way with puzzles from that limitated range. for more used another function
	@staticmethod
	def generate_good_puzzle(puzzle_size, is_basik):
	    basic_puzzle = [
	    [[1, 2],#0
	    [3, 0]], 
	
	    [[1, 2, 3], #1
	    [4, 5, 6],
	    [7, 8, 0]],
	
	    [[1, 2, 3, 4], #2
	    [5, 6, 7, 8],
	    [9, 10, 11, 12],
	    [13, 14, 15, 0]], 
	    
	    [[1, 2, 3, 4, 5], #3
	    [6, 7, 8 , 9, 10],
	    [11, 12, 13, 14, 15],
	    [16, 17, 18, 19, 20],
	    [21, 22, 23, 24, 0]]]
	    
	    snail_puzzle = [
	    [[1, 2], #0
	    [3, 0]], 
	    
	    [[1, 2, 3], #1
	    [8, 0, 4],
	    [7, 6, 5]], 
	
	    [[1, 2, 3, 4], #2
	    [12, 13, 14, 5], 
	    [11, 0, 15, 6], 
	    [10, 9, 8, 7]], 
	
	    [[1, 2, 3, 4, 5], #3 
	    [16, 17, 18, 19, 6], 
	    [15, 24, 0, 20, 7], 
	    [14, 23, 22, 21, 8], 
	    [13, 12, 11, 10, 9]]]
	    return basic_puzzle[puzzle_size - 2] if is_basik else snail_puzzle[puzzle_size - 2]

	@staticmethod
	def generate_basic_big(puzzle_size):
    	#fill line with natural digits from 1 to puzzle_size
		generated_basic_puzzle = [[temp_y + 1 + temp_x * puzzle_size for temp_y in range(puzzle_size)] for temp_x in range(puzzle_size)]
    	#set last symb in the last line with 0
		generated_basic_puzzle[-1][-1] = 0
    	#return generated puzzle
		return generated_basic_puzzle

	@staticmethod
	def big_generation_handler(is_basic, puzzle_size):
		string = f'{"BASIC goal puzzle" if is_basic else "SNAIL goal puzzle"}'
		Printer.logger('debug', f'Generating big puzzle with size {puzzle_size} and it will be {string}')
		generated_goal_puzzle = str()
		if is_basic:
			generated_goal_puzzle = Generator.generate_basic_big(puzzle_size)
		else:
			generated_goal_puzzle = Generator.generate_snail_big(puzzle_size)
		Printer.logger('debug', f'done with it. Result: {generated_goal_puzzle}')
		Printer.debug_print_puzzle(generated_goal_puzzle, puzzle_size)
		return generated_goal_puzzle
   	
	@staticmethod
	def generate_snail_big(puzzle_size):
		puzzle_square_size_ = puzzle_size * puzzle_size
		goal_generated_puzzle = [-1 for i in range(puzzle_square_size_)]
		head = 1
		board_row = 0
		temp_row_id = 1
		board_col = 0
		temp_coll_id = 0

		while 1:
			goal_generated_puzzle[board_row + board_col * puzzle_size] = head
	        
			if head == 0:
				break
	        
			head += 1
			if board_row + temp_row_id == puzzle_size or board_row + temp_row_id < 0 or (temp_row_id != 0 and goal_generated_puzzle[board_row + temp_row_id + board_col * puzzle_size] != -1):
				temp_coll_id = temp_row_id
				temp_row_id = 0
			elif board_col + temp_coll_id == puzzle_size or board_col + temp_coll_id < 0 or (temp_coll_id != 0 and goal_generated_puzzle[board_row + (board_col+temp_coll_id) * puzzle_size] != -1):
				temp_row_id = -temp_coll_id
				temp_coll_id = 0
	
			board_row += temp_row_id
			board_col += temp_coll_id
	        
			if head == puzzle_square_size_:
				head = 0
		
		goal = [goal_generated_puzzle[temp : temp + puzzle_size] for temp in range(0, puzzle_square_size_, puzzle_size)]
		
		return goal

#=======================================================================================
#Class used for some special cases that should be fixed in some magic way
class Crutches:

	#method cover situation when puzzle size = 1
	@staticmethod
	def print_solution_with_size_one():
		Printer.logger('debug', 'Board size = 1. Solution not needed iteration')
		Printer.logger('debug', 'Board looks like:')
		Printer.display_results( '1', 0, 0, 1)

#=======================================================================================
#Class that containing different puzzle map information
class MetaDataMap():
	def __init__(self, map_=[], otcovskii_pazl=None, euristic_h=0, cena_hoda_g=0, total_f=0, poslednii_hod=None):
		self.map_ = map_
		self.otcovskii_pazl = otcovskii_pazl
		self.euristic_h = euristic_h
		self.cena_hoda_g = cena_hoda_g
		self.total_f = total_f
		self.poslednii_hod = poslednii_hod

	def dumpObject(self):
		Printer.logger('debug', f'map_ {self.map_}')
		Printer.logger('debug', f'otcovskii_pazl {self.otcovskii_pazl}')
		Printer.logger('debug', f'heuristic_h {self.euristic_h }')
		Printer.logger('debug', f'cena hoda {self.cena_hoda_g}')
		Printer.logger('debug', f'total_f {self.total_f}')
		Printer.logger('debug', f'poslednii_hod {self.poslednii_hod}')

	def objectCreator(self):
		Printer.logger('debug', 'Objected MetaDataMap created')

	def euristic_calculator(self, zero_coordinate_y, zero_coordinate_x, finish_object, choosen_search, choosen_metric):
		Printer.logger('debug', f'starting calculating euristic with next map {finish_object.map_}, choosen_search {choosen_search}, choosen_metric {choosen_metric}')
		total_heuristic_f = 0

		# trying to handle blind choosen_search (uniform cost a.k.a. brute force machiiine)
		if choosen_search == 3:
			if self.otcovskii_pazl:
				self.cena_hoda_g = self.otcovskii_pazl.move_cost + 1
				self.total_f = self.cena_hoda_g
			else:
				self.total_f = self.cena_hoda_g
		else:
			# Процессим все возможные расчёты евристических дистанций
			for x, tiles_row in enumerate(self.map_):

				for y, tile_value in enumerate(tiles_row):

					if tile_value:
						a, b = Solvable.find_coordinates_of_the_given_digit(tile_value, finish_object.map_)

						if choosen_metric == 1:
                            # манхетенская дистанция
							#Printer.logger('debug', f'calucate map with Manhattan')
							total_heuristic_f += abs(x - a) + abs(y - b)

						elif choosen_metric == 2:
							# эвклидовая дистанция
							#Printer.logger('debug', f'calucate map with Euclidean')
							total_heuristic_f += math.sqrt((x - a)**2 + (y - b)**2)

						elif choosen_metric == 3:
							# чебышева
							#Printer.logger('debug', f'calucate map with Chebyshev')
							total_heuristic_f += max([abs(x - a), abs(y - b)])

						elif choosen_metric == 4:
							# минковски p=4
							#Printer.logger('debug', f'calucate map with Minkowski')
							total_heuristic_f += ((x - a)**4 + (y - b)**4)**0.25

						elif choosen_metric == 5:
							# хамминга
							#Printer.logger('debug', f'calucate map with Hamming')
							if tile_value != finish_object.map_[x][y]:
								total_heuristic_f += 1

						elif choosen_metric == 6:
							# канбера
							#Printer.logger('debug', f'calucate map with Canberra')
							if x or a:
								total_heuristic_f += abs(x-a) / (x+a)
							if y or b:
								total_heuristic_f += abs(y-b) / (y+b)

		self.euristic_h = total_heuristic_f

		# handle choosen_search type 1 standard or 2 greedy
		if choosen_search == 2:
			self.total_f = self.euristic_h
		else:
			if self.otcovskii_pazl:
				self.cena_hoda_g = self.otcovskii_pazl.cena_hoda_g + 1
				self.total_f = total_heuristic_f + self.cena_hoda_g
			else:
				self.total_f = total_heuristic_f

		return self

#=======================================================================================

#Class that process resolving of the puzzle
class SolveManager:

	@staticmethod
	def start_solve(base_map, ideal_map, choosen_metric, choosen_search):
		Printer.logger('debug', "Starting solving")	

		#create data objects where we will save temp values
		start_object = MetaDataMap(map_=base_map)
		finish_object = MetaDataMap(map_=ideal_map)

		finish_zero_coordinate_y, finish_zero_coordinate_x = Solvable.find_coordinates_of_the_given_digit(0, ideal_map)
		search = choosen_search
		metric = choosen_metric
		
		#init calculation of the input map
		start_object = start_object.euristic_calculator(finish_zero_coordinate_y, finish_zero_coordinate_x, finish_object, search, metric)
	
		#print status to the debug logs
		start_object.objectCreator()
		start_object.dumpObject()

		exit(1)
		# max_total_cost = start_puzzle.total_cost
		# z_a, z_b = _get_tile_coordinates(0, finish_puzzle)
	
		# complexity_time = 0
		# max_size = 0
	 #    while 1:
	 #        complexity_size = 1
	 #        puzzle, new_total_cost, complexity_time, complexity_size = _ida_recursive_search(start_puzzle, max_total_cost, z_a, z_b, complexity_time, complexity_size, metric, finish_puzzle, n, search)
	
	 #        if max_size < complexity_size:
	 #            max_size = complexity_size
	
	 #        if puzzle != None:
	 #            _print_solution(puzzle, complexity_time, max_size, start_time)
	 #            return
	
	 #        if new_total_cost == math.inf:
	 #            return
	
	 #        max_total_cost = new_total_cost


#utility function that actually start command line parser
def command_line_parsing():
    global DEBUG
    args = parser.parse_args()
    DEBUG = args.debug
    return args

def main(args):
	#step #2: read from file, with error checking or without, flag required
	#default: read without error handling
	if (args.error):
		puzzle_size, puzzle = Reader.errors_check_read(args.file)
	else:
		puzzle_size, puzzle = Reader.simple_read(args.file)

	#step #3: depend on different puzzle size please call proper function that will generate goal puzzle
	if puzzle_size != 0:
		if puzzle_size == 1:
			#ToDo: Done. small function that will print 1 and complexity time blablabla
			Crutches.print_solution_with_size_one()
		
		if puzzle_size in range(2, 6):
			good_puzzle = Generator.generate_good_puzzle(puzzle_size, args.basic)
			Printer.logger('debug', 'Generated good puzzle')
			string = f'Puzzle with format: {"basic goal puzzle" if args.basic else "snail goal puzzle"}'
			Printer.logger('debug', string)
			Printer.logger('debug', good_puzzle)
			Printer.logger('debug', "Normalize view of the puzzle")
			Printer.debug_print_puzzle(good_puzzle, puzzle_size)
		
		if puzzle_size > 5:
			#ToDo: done. add function that will generate puzzle with len > 5
			Generator.big_generation_handler(args.basic, puzzle_size)

		Printer.logger('term', "Received puzzle:")
		Printer.print_puzzle(puzzle, puzzle_size)
		Printer.logger('term', "Goal puzzle: ")
		Printer.print_puzzle(good_puzzle, puzzle_size)
		if (Solvable.can_solve(puzzle, good_puzzle) == False):
				print ("Dummy. It cant be solved, check again provided puzzle and also check flag --basic")
				return False
#      npuzzle(puzzle, good_puzzle, args.metric, args.search, args.visual)
		SolveManager.start_solve(puzzle, good_puzzle, args.metric, args.search)

if __name__ == "__main__":
	#step #1. parse command line arguements, for future manipulations
    main( command_line_parsing() )
