import os
import sys
import logging
import datetime

from configuration import config

logging.basicConfig(level=logging.INFO, format='%(asctime)-12s %(levelname)-8s %(message)s')

class aws_logging(object):

	def create_log(self, logging_level, logging_message):
		if config['logging'] != True:
			return;

		if logging_level == "error":
			logging.error(logging_message)
		else:
			logging.info(logging_message)