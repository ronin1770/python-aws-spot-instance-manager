"""
	Prerequisite: Please ensure you have created aws credentials/configuration file in /home/<Your Username>/.aws/credentials
	Preferred OS: Ubuntu / Linux
	

"""

import os
import sys
import boto3
from botocore.exceptions import ClientError
import csv
import datetime
import time

from configuration import config
from aws_security_group import *
from aws_logging import *

class aws_spot_instance_manager(object):

	_ec2_types = {}
	_aws_sg    = None
	_logging   = None

	#Constructor
	def __init__(self):
		# Create the resource for EC2 creator
		if self.check_aws_configuration_exists() == False:
			self.create_log( "error", "AWS Credentials file not found")
			sys.exit(0)

		if self.load_ec2_info() == False:
			self.create_log("error", "Loading EC2 Information failed")
			sys.exit(0)

		self._aws_sg = aws_security_group()
		self._logging = aws_logging()
		vps = self._aws_sg.get_VPCs("us-east-1")

	#Check if the AWS configuration file exists - it not throw an error
	# It should exist in ~/.aws/credentials 
	def check_aws_configuration_exists(self):
		return os.path.isfile(config['aws_creds_location'])

	
	def create_security_group(self, sg_name, sg_description, rules):
		#Get the Security Group ID
		sg_id = self._aws_sg.create_security_group("Boto_SG", "created using Boto", rules, None)
		return sg_id

	# ami_id  => The ID of the AMI
	# keypair_name => Name of the keypair for authentication (String)
	# instance_type => Updated list https://aws.amazon.com/ec2/instance-types/ (String)
	# Min count = Minimum number of instances  (int)
	# Max count = Maximum number of instances  (int)
	# Monitoring = Monitoring (boolean)
	# sg_id = Security Group ID
	# shutdown behavior = 'stop' | 'terminate'
	# 
	def create_instance(self, ami_id, keypair_name, instance_type, min_count, max_count, monitoring, sg_id, shutdown_behavior ):
		ret = None
		ec2 = boto3.resource('ec2')

		subnet_ids = self._aws_sg.get_subnet_id()

		if len(subnet_ids) < 1:
			self._logging.create_log("info", "No subnets found in" + self.create_instance.__name__  +   " exiting...")
			return



		try:
			ret = ec2.create_instances(
				ImageId = ami_id,
				MinCount = min_count,
				MaxCount = max_count,
				InstanceType = instance_type,
				KeyName = keypair_name,
				Monitoring = { 'Enabled' : monitoring },
				SecurityGroupIds = [ sg_id ],
				SubnetId=subnet_ids[0]
				)

		except Exception as e:
			self._logging.create_log("error", "Error in " + self.create_instance.__name__  +   ": " + str(e) + "\n")	


		return ret

	#Method to get AMI's details	
	def get_AMI_details(self, ami_id):
		ret = None
		ec2 = boto3.resource('ec2', region_name=config['region'] )
		client = boto3.client('ec2')

		try:
			response = client.describe_images(
				ImageIds = [ami_id]
			)

			ret = response
		except Exception as e:
			self._logging.create_log("error", "Error in " + self.get_AMI_details.__name__  +   ": " + str(e) + "\n")	

		return ret

	#TODO:
	def create_keypair(self, keypair_name, keypair_description):
		return None


	#TODO	
	#Get the list of AMI's for given OS type
	#For time being it is assumed that consumer will provide the AMI-ID
	def get_AMIs_By_OS(self, OS_name, Limit):
		None

	#Get the spot price using Boto3 SDK
	#os_type = Linux/UNIX'|'Linux/UNIX (Amazon VPC)'|'Windows'|'Windows (Amazon VPC)'
	def get_ec2_spot_price(self, instance_type, num_results, os_type, region_name):
		inst_type = []
		os_types = []
		inst_type.append(instance_type)
		os_types.append(os_type)
		start_date = datetime.datetime.now() - datetime.timedelta(90)
		end_date = datetime.datetime.now() - datetime.timedelta(0)
		availability_zone = region_name + "a"
		count = 0
		ret = []

		try:
			client=boto3.client('ec2',region_name=config['region'])
			paginator = client.get_paginator('describe_spot_price_history') 
			page_iterator = paginator.paginate(InstanceTypes =inst_type,ProductDescriptions = os_types, AvailabilityZone = availability_zone ) 

			for page in page_iterator: 
				self._logging.create_log( "info", "Number of results: " + str(len(page['SpotPriceHistory']) ) )

				for x in range( len(page['SpotPriceHistory'])):
					if count > num_results:
						break
					ret.append(page['SpotPriceHistory'][x])	
		except Exception as e:
			self._logging.create_log( "error", "Issue gettomg ec2 spot price: " + str(e) )
			return None
		return ret

	#Method for terminating running EC2 instances (CAUTION - use with care)
	#Input argument: list containing the instance ids to be terminated
	def terminate_ec2_instance(self, instances):
		try:
			client=boto3.client('ec2',region_name=config['region'])
			return client.terminate_instances( InstanceIds=instances )

		except Exception as e:
			self._logging.create_log("error", "Error in " + self.stop_ec2_instances.__name__  +   ": " + str(e) + "\n")	
			return None

	#Method for stopping running EC2 instances
	#Input argument: list containing the instance ids 
	#Syntax instances = [ 'dsdfsdfds','sdfffs', 'sdfdfdsfs']
	def stop_ec2_instances(self, instances):
		try:
			client=boto3.client('ec2',region_name=config['region'])
			return client.stop_instances( InstanceIds=instances )

		except Exception as e:
			self._logging.create_log("error", "Error in " + self.stop_ec2_instances.__name__  +   ": " + str(e) + "\n")	
			return None


	#Function for loading EC2 instances 
	#As of June-2020 there is no API method to get list of EC2 types
	#Created method to convert CSV to JSON object
	#Download csv from https://www.ec2instances.info/ (renmed the file to ec2_info.csv)
	def load_ec2_info(self):
		try:
			with open( config['ec2_info_csv']) as csvfile:
				readCSV = csv.reader(csvfile, delimiter=",")
				for row in readCSV:
					self._ec2_types[row[1]]  = { "name" : row[1], "memory" : row[2], "cpus" : row[3], "storage" : row[4]}
		except Exception as e:
			self._logging.create( "error", "Issue loading ec2_info: " + str(e) )
			return False
		return True	

if __name__ == "__main__":
	#Allow SSH from specific IP
	#Allow Web acccess globally
	rules = [ { 'FromPort':22, 'ToPort' : 22, 'IpProtocol':'tcp', 'IpRanges':[ {'CidrIp':'x.x.x.x/32', 'Description':'SSH access from Home'}] },  
				{ 'FromPort':80, 'ToPort' : 80, 'IpProtocol':'tcp', 'IpRanges':[ {'CidrIp':'0.0.0.0/0', 'Description':'Global web access'}] }
			]


	mgr = aws_spot_instance_manager()

	#Ubuntu 18
	ami_id = "ami-07d0cf3af28718ef8"

	#Keypair name
	keypair_name = "dta"

	#Instance Type
	instance_type = "t3.micro"

	#Min number of instances
	min_count = 1

	#Max number of instances
	max_count = 1

	#Enable monitoring
	monitoring = False

	#Securitry group name
	sg_name = "Boto_SG"

	#Security Group description
	sg_description = "Testing creation of Security Group using Boto3 Python Library"

	sg_id = mgr.create_security_group(sg_name, sg_description, rules)

	#Shutdown behavior - stop the instance on shut down
	shutdown_behavior = "stop"

	if( sg_id == None):
		mgr._logging.create_log("INFO", "No security group is found or can be created. Check your permissions")
		sys.exit(0)
	

	instances = mgr.create_instance(ami_id, keypair_name, instance_type, min_count, max_count, monitoring, sg_id, shutdown_behavior )

	mgr._logging.create_log("INFO", "Instances created\n" + str(instances) + "\n---------------------\n" )