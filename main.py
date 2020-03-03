from datetime import datetime as dt
import copy
import sys
import argparse
import math
import heapq as heap_queue_algorithm
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
	def get_list_node(final_graph_node):
		print (final_graph_node)
		global_set = []

		while final_graph_node:
			global_set.insert(0, final_graph_node)
			final_graph_node = final_graph_node.otcovskii_pazl
		return global_set

	@staticmethod
	def print_list_node(global_set):
		for tekushii_pazl in global_set:
			for ryad in tekushii_pazl.map_:
				Printer.logger('term', ' '.join(map(str, ryad)))
			Printer.logger('term', ' ')
		return (len(global_set))

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
		steps = Printer.print_list_node( Printer.get_list_node(moves_to_finish) )
	    # # if visualization == True:
	    # #     Printer.step_visualization(moves_to_finish.map_)
	    print (parser.visual)
		Printer.logger('term', f"complex time: {str(complexTime)}")
		Printer.logger('term', f"complex size: {str(complexSize)}")
		Printer.logger('term', f"total steps: {str(steps)}")
	    # #Printer.logger('term', f"how many steps required: {str(len(moves_to_finish) - 1)}")
	    # Printer.logger('term', f"full program time: {str(dt.now() - start_time)}")

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
	def __hash__(self):
		return hash(str(self.map_))

	def __eq__(self, other):
		if isinstance(other, self.__class__):
			return self.map_ == other.map_
		return False

	def __lt__(self, other):
		if isinstance(other, self.__class__):
			return self.total_f < other.total_f
		return False

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
		Printer.logger('debug', f'starting calculating euristic with next map {self.map_}, choosen_search {choosen_search}, choosen_metric {choosen_metric}')
		total_heuristic_f = 0

		# trying to handle blind choosen_search (uniform cost a.k.a. brute force machiiine)
		if choosen_search == 3:
			if self.otcovskii_pazl:
				self.cena_hoda_g = self.otcovskii_pazl.cena_hoda_g + 1
				self.total_f = self.cena_hoda_g
			else:
				self.total_f = self.cena_hoda_g
		else:
			# Процессим все возможные расчёты евристических дистанций
			for x, stroki_map in enumerate(self.map_):

				for y, znachenie_stroki in enumerate(stroki_map):

					if znachenie_stroki:
						a, b = Solvable.find_coordinates_of_the_given_digit(znachenie_stroki, finish_object.map_)

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
							if znachenie_stroki != finish_object.map_[x][y]:
								total_heuristic_f += 1

						elif choosen_metric == 6:
							# канбера
							#Printer.logger('debug', f'calucate map with Canberra')
							
							if x or a:
								total_heuristic_f += abs(x-a) / (x+a)
							
							if y or b:
								total_heuristic_f += abs(y-b) / (y+b)

		self.euristic_h = total_heuristic_f

		# чекни тут стандартный поиск и еще гриди сьорч (2ечка)

		if choosen_search == 2:
			self.total_f = self.euristic_h
		
		else:
			#//checkai default algo
			if self.otcovskii_pazl:

				self.cena_hoda_g = self.otcovskii_pazl.cena_hoda_g + 1

				self.total_f = total_heuristic_f + self.cena_hoda_g
		
			else:
			#kostyl na init iteraciyu
				self.total_f = total_heuristic_f
		#vozvrashai object na bazu
		return self

#=======================================================================================

#Class that process resolving of the puzzle
class SolveManager:

	#naidi luchshii solution v close set, i verni ego
	@staticmethod
	def check_best_variant_in_close_set(tekushii_pazl=None, close_set={}):
		# print (tekushii_pazl)
		# print (close_set)
		# if tekushii_pazl in close_set:
		# 	print ("ABBRAAA")
		# 	for i in close_set:
		# 		print (i)
		# 	print (close_set[tekushii_pazl])
		return tekushii_pazl in close_set and close_set[tekushii_pazl] <= tekushii_pazl.total_f

	@staticmethod
	def main_a_star_algorithm(start_object, finish_object, metric=1, search=1):
		finish_zero_coordinate_y, finish_zero_coordinate_x = Solvable.find_coordinates_of_the_given_digit(0, finish_object.map_)
		#start_object = start_object.euristic_calculator(finish_zero_coordinate_y, finish_zero_coordinate_x, finish_object, search, metric)

		Printer.logger('debug', 'DONE ONCE WITH EURISTIC')

		open_set = []
		heap_queue_algorithm.heappush(open_set, start_object)
		close_set = {}
		time_complex = size_complex = 0
		len_of_map = len(start_object.map_)
		while 1:
			if not open_set:
				print('NOT FOUND', start_object.map_)
				return

			tekushii_pazl = heap_queue_algorithm.heappop(open_set)
        
			time_complex += 1
			if len(open_set)+len(close_set) > size_complex:
				size_complex = len(open_set) + len(close_set)

			if tekushii_pazl == finish_object:
				Printer.logger('debug', 'Finally, find path to the final, bro!')
				Printer.display_results(tekushii_pazl, time_complex, size_complex, 1)
				return

			if not SolveManager.check_best_variant_in_close_set(tekushii_pazl, close_set):
				Printer.logger('debug', 'WE ARE CREATING NEW CHILDS')
				close_set[tekushii_pazl] = tekushii_pazl.total_f
				nasledniki = SolveManager.create_naslednikov(tekushii_pazl, len_of_map)
			
				for naslednik in nasledniki:
					Printer.logger('debug', 'adding naslednikov v HEAP')
					a = naslednik.euristic_calculator(finish_zero_coordinate_y, finish_zero_coordinate_x, finish_object, search, metric)
					heap_queue_algorithm.heappush(open_set, a)

	#obertka dlya osnovnogo rekursivnogo solvera
	@staticmethod
	def start_solve(base_map, ideal_map, choosen_metric, choosen_search):
		Printer.logger('debug', "Starting solving")	
		recursive = False


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

		summary_cost = start_object.total_f
		finish_zero_coordinate_y, finish_zero_coordinate_x = Solvable.find_coordinates_of_the_given_digit(0, finish_object.map_)
	
		time_complex = 0
		size_max = 0
		len_of_map = len(start_object.map_)
		
		SolveManager.main_a_star_algorithm(start_object, finish_object, choosen_metric, choosen_search)

		exit(1)
		if (recursive == True):
			Printer.logger('debug', 'You have tried to use recursive search, bro, have fun :d')
			Printer.logger('debug', "Entered main solver search loop")
			while True:
				size_complex = 1
				puzzle, updated_summary_cost, time_complex, size_complex = SolveManager.searching_step(start_object, summary_cost, finish_zero_coordinate_y, finish_zero_coordinate_x, time_complex, size_complex, metric, finish_object, len_of_map, search)
				if size_max < size_complex:
					size_max = size_complex
				if puzzle != None:
					print ("RECURSIVE SEARCH DONE:DD EXITING")
					exit(1)
					return
				if updated_summary_cost == math.inf:
					return
				summary_cost = updated_summary_cost

#Internal variables from MetaData class
#map_ = map_
#otcovskii_pazl = otcovskii_pazl
#euristic_h = euristic_h
#cena_hoda_g = cena_hoda_g
#total_f = total_f
#poslednii_hod = poslednii_hod

	@staticmethod
	def searching_step(map_object, summary_cost, finish_zero_coordinate_y, finish_zero_coordinate_x, time_complex, size_complex, metric, finish_object, len_of_map, search):
#method kotorii delaet vsyu robotu, generit naslednikov, delaet hod, obnovlyaet vesa, cennosti hodov i tak dalee
		print ('zashel v searching_step')
		if map_object.total_f > summary_cost:
			return None, map_object.total_f, time_complex, size_complex

		time_complex += 1
		if map_object == finish_object:
			return map_object, summary_cost, time_complex, size_complex

		minimalnii_cost = math.inf
		nasledniki = SolveManager.create_naslednikov(map_object, len_of_map)
		size_complex += len(nasledniki) #kolli4estvo osmotrenih hodov
		
		#debug logi na proverochku naslednikov
		# for i in nasledniki:
		# 	i.dumpObject()

		for naslednik in nasledniki:
			naslednik = naslednik.euristic_calculator(finish_zero_coordinate_y, finish_zero_coordinate_x, finish_object, search, metric)
			tekushii_pazl, novyi_cost, time_complex, size_complex = SolveManager.searching_step(naslednik, summary_cost, finish_zero_coordinate_y, finish_zero_coordinate_x, time_complex, size_complex, metric, finish_object, len_of_map, search)

			if tekushii_pazl != None:
				return tekushii_pazl, None, time_complex, size_complex

			if novyi_cost < minimalnii_cost:
				minimalnii_cost = novyi_cost

		return None, minimalnii_cost, time_complex, size_complex



	@staticmethod
	def prepare_move_up(object_entity, x , y ):
		karta = copy.deepcopy(object_entity.map_)
		karta[x][y], karta[x+1][y] = karta[x+1][y], karta[x][y]
		naslednik = MetaDataMap(map_=karta, otcovskii_pazl=object_entity)
		naslednik.poslednii_hod = 'up'
		return naslednik
	
	@staticmethod
	def prepare_move_down(object_entity, x , y ):
		karta = copy.deepcopy(object_entity.map_)
		karta[x][y], karta[x-1][y] = karta[x-1][y], karta[x][y]
		naslednik = MetaDataMap(map_=karta, otcovskii_pazl=object_entity)
		naslednik.poslednii_hod = 'down'
		return naslednik

	@staticmethod
	def prepare_move_left(object_entity, x , y ):
		karta = copy.deepcopy(object_entity.map_)
		karta[x][y], karta[x][y+1] = karta[x][y+1], karta[x][y]
		naslednik = MetaDataMap(map_=karta, otcovskii_pazl=object_entity)
		naslednik.poslednii_hod = 'left'
		return naslednik
	
	@staticmethod
	def prepare_move_right(object_entity, x , y ):
		karta = copy.deepcopy(object_entity.map_)
		karta[x][y], karta[x][y-1] = karta[x][y-1], karta[x][y]
		naslednik = MetaDataMap(map_=karta, otcovskii_pazl=object_entity)
		naslednik.poslednii_hod = 'right'
		return naslednik

	@staticmethod
	def create_naslednikov(start_object, len_of_map):
		nasledniki = []
		x, y = Solvable.find_coordinates_of_the_given_digit(0, start_object.map_)

		print (f"LEN OF MAP: {len_of_map}, x: {x}, y: {y}")
		if x+1 < len_of_map and start_object.poslednii_hod != 'down':
			nasledniki.append( SolveManager.prepare_move_up(start_object, x, y) )

		if x-1 >= 0 and start_object.poslednii_hod != 'up':
			nasledniki.append( SolveManager.prepare_move_down(start_object, x, y) )

		if y+1 < len_of_map and start_object.poslednii_hod != 'right':
			nasledniki.append( SolveManager.prepare_move_left(start_object, x, y) )

		if y-1 >= 0 and start_object.poslednii_hod != 'left':
			nasledniki.append( SolveManager.prepare_move_right(start_object, x, y) )

		for i in nasledniki:
			i.dumpObject()

		return nasledniki
#Internal variables from MetaData class
#map_ = map_
#otcovskii_pazl = otcovskii_pazl
#euristic_h = euristic_h
#cena_hoda_g = cena_hoda_g
#total_f = total_f
#poslednii_hod = poslednii_hod


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
