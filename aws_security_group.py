import os
import sys
import boto3
from botocore.exceptions import ClientError
import csv
import datetime

from aws_logging import *
from configuration import config

class aws_security_group(object):

	_vpcs = []
	_logging = None

	def __init__(self):
		self._logging = aws_logging()

	def get_VPCs(self, region_name):
		self._logging.create_log("info", "Getting the VPCs")
		vps = []

		ec2 = boto3.resource('ec2', region_name=region_name )
		client = boto3.client('ec2')

		try:
			response = client.describe_vpcs()
			vpcs = response.get('Vpcs', [{}])
			return vpcs
		except Exception as e:
			self._logging.create_log("error", "Error while getting the VPCs Information:" + (str(e)) )
			return None

	def get_subnet_id(self):
		vpcs = self.get_VPCs(config['region'])
		if vpcs == None:
			self._logging.create_log("error", "Error while getting the VPCs Information:" + (str(e)) )
			return None

		vpc_id = self.get_specific_vpc(vpcs);		

		if vpc_id == None:
			self._logging.create_log("error", "Error while trying to find the vpc_id:" + (str(e)) )
			return None

		session = boto3.Session(region_name=config['region'])
		ec2_resource = session.resource("ec2")
		ec2_client = session.client("ec2")
		subnet_ids = []
		for vpc in ec2_resource.vpcs.all():
			if vpc.id == vpc_id['VpcId']:
				for subnet in vpc.subnets.all():
					subnet_ids.append(subnet.id)
		return subnet_ids

	# Create default VPC needed - if there are no VPCs default - it will not work for that region		
	# method returns the specific VPC specified by its vpc_id
	# otherwise it returns the default VPC
	# In case there is no default VPC - it will create a default VPC and return it
	def get_specific_vpc(self, vpcs, vpc_id=None):
		ret = None

		for x in range( len( vpcs)):

			if vpc_id != None:
				if vpc_id == vpcs[x]['VpcId']:
					ret = vpcs[x]
					break
			else:
				if vpcs[x]['IsDefault']	== True:
					ret = vpcs[x]
					break

		if ret == None:
			try:
				#Create the default VPC
				client = boto3.client('ec2', region_name = config['region']) # Adjust as desired
				ret = client.create_default_vpc()
				self._logging.create("Created Default VPC" + str(ret))
			except Exception as e:
				#In case of Classic-EC2 default VPC creation is not permitted
				# Reference: https://docs.aws.amazon.com/vpc/latest/userguide/default-vpc.html
				self._logging.create_log("error", "Error in " + self.get_specific_vpc.__name__  +   " while creating default VPC: " + str(e) + "\n")	
				#TODO:
				#Create default VPC 
				if len(vpcs) > 0:
					ret = vpcs[0]

		return ret


	#Checks if Security Group exists by using its name
	def get_security_group_by_name(self, security_group_name):
		ret = None
		try:

			client = boto3.client('ec2')	
			response = client.describe_security_groups(
			    Filters=[
			        dict(Name='group-name', Values=[security_group_name])
				    ]
			)

			if len(response['SecurityGroups']) > 0:
				self._logging.create_log("info", "Security Group: " + security_group_name + " exists")
				ret = response['SecurityGroups'][0]['GroupId']
		except Exception as e:
			self._logging.create_log("error", "Error in " + self.get_specific_vpc.__name__  +   " while gettting VPC Info: " + str(e) + "\n")	

		return ret





	# Create a Security Group using the Default VPC ID
	#security_group_name = String
	#security_grup_description = String
	#rules = [ { "IpProtocol" : "tcp/udp", "FromPort" : "<NUMBER>", "ToPort" : "<NUMBER>", "IpRanges" : [{'CidrIp' : '0.0.0.0/0'}]} ]
	#vpc_id = Specific VPC to be used identified by vpc_id
	def create_security_group(self, security_group_name, security_group_description, rules, vpc_id=None):
		sg_id = self.get_security_group_by_name(security_group_name)

		if sg_id != None:
			return sg_id

		vps = []

		ec2 = boto3.resource('ec2', region_name=config['region'])
		client = boto3.client('ec2')

		try:
			vpcs = self.get_VPCs(config['region'])
			selected_vpc = self.get_specific_vpc(vpcs)
			
			if selected_vpc == None:
				self._logging.create_log("info", "No VPCs found in this region(" + config['region'] + "). Please select another region.")
				return

			vpc_id = selected_vpc['VpcId']	

			sec_group = client.create_security_group( GroupName=security_group_name, Description=security_group_description, VpcId=vpc_id)

			#sec_group.authorize_ingress( DryRun = False, IpPermissions = rules)
			client.authorize_security_group_ingress(GroupId=sec_group['GroupId'], IpPermissions=rules)

			return sec_group['GroupId']

		except Exception as e:
			self._logging.create_log("error", "Error in "+ self.create_security_group.__name__ +" Information:" + (str(e)) )
			return None	