# python-aws-spot-instance-manager
This library provides an easy interface for managing AWS Spot Instances

<B>Test Environment</B>

Code is tested on <B>Python version 3.6.9</B> and <B>Ubuntu 18.04</B> operating system.

<B>AWS Credentials File</B>
Syntax for AWS Credentials file can be found here: https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html


<B>Installation</B>

  Please clone the library using your preferred GIT software
  
  On command line please follow these steps:
  
    - Open the terminal
    - Browse to the folder where you want to install the library
    - Type: 
  
        git clone https://github.com/ronin1770/python-aws-spot-instance-manager.git
  
  This will create a folder inside your selected folder called 'python-aws-spot-instance-manager'. Folder will have following contents:
  
    -rw-rw-r-- 1 fm fm    413 Jun 14 08:38 aws_logging.py
    -rw-rw-r-- 1 fm fm   4639 Jun 28 11:48 aws_security_group.py
    -rw-rw-r-- 1 fm fm   8031 Jun 28 12:27 aws-spot-instance-manager.py
    -rw-rw-r-- 1 fm fm    329 Jun 28 12:32 configuration.py
    -rw-rw-r-- 1 fm fm 199011 Jun  9 21:51 ec2_info.csv
    -rw-r--r-- 1 fm fm    107 Jun 28 12:30 README.md

<B>Usage</B>

Sample code that start / stop / terminate instances is included. Please open up <I>aws-spot-instance-manager.py</I> in your favorite code editor. Please browse to the section that says:

    if __name__ == "__main__":
    
Code after this is self explanatory. Please note in the example, we create:

1. Simple Security group called (Boto_SG)

2. Boto_SG allows access for a specific IP to SSH

Please ensure you use <B>Your OWN IP Address (instead of x.x.x.x)</B> else you will not be able to SSH into it. 

    rules = [ { 'FromPort':22, 'ToPort' : 22, 'IpProtocol':'tcp', 'IpRanges':[ {'CidrIp':'x.x.x.x/32', 'Description':'SSH access from Home'}] },  
		    		{ 'FromPort':80, 'ToPort' : 80, 'IpProtocol':'tcp', 'IpRanges':[ {'CidrIp':'0.0.0.0/0', 'Description':'Global web access'}] }
		]

3. Test instance is of Linux type

4. Code for stopping and terminating is commented. Please un-comment the desired operation. 


