# ur_modbus_opcua
An interface developed as an OPC/UA interface for the UR10e by communicating over Modbus TCP. 

# Installation

After installing [Python Version 3.11.9](https://www.python.org/downloads/release/python-3119/), clone the repository to "C:\", and install the required dependencies using 

```
pip install -r requirements.txt
```

Follow [these instructions](https://help.thinkiq.com/knowledge-base/data-connectivity/gateways-connectors/gateway-connectors-setup) to install the OPCUA connector to get data into the SMIP 

Follow the instructions in [this guide](https://www.computerhope.com/issues/ch000322.htm#:~:text=Run%20a%20batch%20file%20at%20loading%20of%20Windows%208%20and%2010&text=Press%20Start%2C%20type%20Run%2C%20and,file%20into%20the%20Startup%20folder.) to add the startup script to run on boot. Note: If there is more than one user on the computer, this method will require a user to sign in before the script is run.

UA Expert can be installed and run on the host machine to verify that the OPC UA output is functioning.

While not required for the ThinkIQ connector, credentials can be generated using the "gen_cridential.py" script included in the repository.

# Program Modification

If the IP address of the robot changes, the python script will need to be updated accordingly. On line 29, the address of the UR10e can be set by changing the "UR10e_MODBUS_IP" variable to the IP address of the machine.

In order to change the parameters being read from the robot, you can modify the dictionary titled "MODBUS_REGISTERS" starting on line 33. Additional attribute names, along with the relevant Modbus TCP/IP register can be added to the end of this dictionary.

The wait period between measurements is approximately 0.5 seconds by default. This can be changed by changing the delay about in line 212 of the server script.

# Known Errors 
1. North Service Fails to Start
   - Ensure that .NET dependencies in the connector documentation are properly installed.
  
Developed for the Advanced Manufacturing Processes and Systems course at Rensselaer Polytechnic Institute by the Digital Manufacturing Project Team:
- Brian Cooper
- Julia Gizzo
- Jack Marcotte
- Kaitlin McConnon
- Jaden Mirek
