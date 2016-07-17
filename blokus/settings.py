from __future__ import division

import numpy as np
import copy

from kivy.config import Config
from kivy.core.window import Window


class Settings(object):
	"""
	this is an object to house some of the
	specific constants that are necessary
	to instantiate the game.
	"""
	screen_size = {'all_players'  : (600, 600),
	 			   'single_player': (300, 600)}

	grid_size   = {'all_players'  : (42, 42),
				   'single_player': (20, 20 + 17)}

	def __init__(self,
				 screen_mode='all_players',
				 num_players=4,
				 num_pieces=21,
				 board_size=20,
				 screen_size=None,
				 grid_size=None,
				 frame_rate=1/60.0,
				 player_types=None,
				 player_strategies=None,
				 player_weights=None,
				 show_all=True,
				 **kwargs):
		"""
		inputs:
		"""

		self.screen_mode = screen_mode
		self.num_players = num_players
		self.num_pieces  = num_pieces
		self.board_size  = board_size
		self.frame_rate  = frame_rate
		self.show_all    = show_all

		self.set_player_properties(
							  player_types,
							  player_strategies,
							  player_weights)

		if screen_size is not None:
			if isinstance(screen_size, dict):
				for k, v in screen_size.items():
					self.screen_size[k] = v
			else:
				self.screen_size[self.screen_mode] = screen_size

		if grid_size is not None:
			if isinstance(grid_size, dict):
				for k, v in grid_size.items():
					self.grid_size[k] = v
			else:
				self.grid_size[self.screen_mode] = grid_size

		self.current_screen_size = self.screen_size[self.screen_mode]
		self.current_grid_size   = self.grid_size[self.screen_mode]

		self.get_block_length()
		self.set_screen()


	def get_block_length(self):

		size_ratio = [screen_size / grid_size
					  for screen_size, grid_size in 
					  zip(self.current_screen_size,
					  	  self.current_grid_size)]

		self.d = int(np.floor(min(size_ratio)))

		if   self.screen_mode == 'all_players':
			corner_offset = [(self.current_grid_size[0]-self.board_size)/2,
							 (self.current_grid_size[1]-self.board_size)/2]
		elif self.screen_mode == 'single_player':
			self.piece_offset = [float((screen_size - grid_size * self.d) / (2 * self.d))
								 for screen_size, grid_size
								 in zip(self.current_screen_size,
								 	    self.current_grid_size)]
			corner_offset = copy.copy(self.piece_offset)
			corner_offset[1] = self.current_screen_size[1] / self.d - corner_offset[1] - self.board_size

		self.corner_offset = corner_offset
		self.board_size_d = int(self.board_size * self.d)
		self.corner_offset_d = [int(location * self.d)
								for location in self.corner_offset]

	def set_screen(self):
		Window.size = self.current_screen_size
		Config.set('graphics', 'width',  self.current_screen_size[0])
		Config.set('graphics', 'height', self.current_screen_size[1])

	def set_player_properties(self, 
							  player_types,
							  player_strategies,
							  player_weights):

		if player_types is None:
			player_types = ['ai'] * self.num_players
		self.player_types = player_types

		if player_strategies is None:
			player_strategies = ['third'] * 3 + ['dual rule']
		self.player_strategies = player_strategies

		if player_weights is None:
			player_weights =   [[1, 0, .5, 0, 3, 2], 
								[2, 0, 2, 0, 1, 3], 
								[2, 2, 2, 0, 2, 2], 
								[1, 2, 2, .5, 20, 10]]
		self.player_weights = player_weights
