# Generated by ChatGPT
# Modified by the AMPS F24 Digital Manufacturing Team
#   -Brian Cooper
#   -Julia Gizzo
#   -Jack Marcotte
#   -Kaitlin McConnon
#   -Jaden Mirek

import asyncio
from pymodbus.client import AsyncModbusTcpClient
import pymodbus
from asyncua import Server
from asyncua import ua
from asyncua.server.user_managers import CertificateUserManager
from asyncua.crypto.cert_gen import setup_self_signed_certificate
import logging
from pathlib import Path
from cryptography.x509.oid import ExtendedKeyUsageOID
import socket
from asyncua.crypto import uacrypto
from asyncua.server.users import User, UserRole

logging.basicConfig(level=logging.WARN)

class UserManager:
    def get_user(self, iserver, username=None, password=None, certificate=None):
        return User(role=UserRole.Admin)
# Configuration for the UR10e Modbus
UR10e_MODBUS_IP = '128.113.220.57'  # UR10e IP Address
MODBUS_PORT = 502                 # Standard Modbus TCP Port

# Define Modbus register ranges for UR10e robot data
MODBUS_REGISTERS = {
    "ActualJointPosition_0": [270],
    "ActualJointPosition_1": [271],
    "ActualJointPosition_2": [272],
    "ActualJointPosition_3": [273],
    "ActualJointPosition_4": [274],
    "ActualJointPosition_5": [275],
    "ActualJointVelocity_0": [280],
    "ActualJointVelocity_1": [281],
    "ActualJointVelocity_2": [282],
    "ActualJointVelocity_3": [283],
    "ActualJointVelocity_4": [284],
    "ActualJointVelocity_5": [285],
    "JointCurrent_0": [290],
    "JointCurrent_1": [291],
    "JointCurrent_2": [292],
    "JointCurrent_3": [293],
    "JointCurrent_4": [294],
    "JointCurrent_5": [295],
    "JointTemperature_0": [300],
    "JointTemperature_1": [301],
    "JointTemperature_2": [302],
    "JointTemperature_3": [303],
    "JointTemperature_4": [304],
    "JointTemperature_5": [305],
    "JointRevolutionCount_0": [320],
    "JointRevolutionCount_1": [321],
    "JointRevolutionCount_2": [322],
    "JointRevolutionCount_3": [323],
    "JointRevolutionCount_4": [324],
    "JointRevolutionCount_5": [325],
    "JointMode_0": [310],
    "JointMode_1": [311],
    "JointMode_2": [312],
    "JointMode_3": [313],
    "JointMode_4": [314],
    "JointMode_5": [315],
    "ToolPosition_X": [400],
    "ToolPosition_Y": [401],
    "ToolPosition_Z": [402],
    "ToolOrientation_rX": [403],
    "ToolOrientation_rY": [404],
    "ToolOrientation_rZ": [405],
    "ToolSpeed_X": [410],
    "ToolSpeed_Y": [411],
    "ToolSpeed_Z": [412],
    "ToolSpeed_rX": [413],
    "ToolSpeed_rY": [414],
    "ToolSpeed_rZ": [415],
    "ToolOffset_X": [420],
    "ToolOffset_Y": [421],
    "ToolOffset_Z": [422],
    "ToolOffset_rX": [423],
    "ToolOffset_rY": [424],
    "ToolOffset_rZ": [425],
    "ToolMode": [768],
    "ToolTemp": [769],
    "ToolCurrent": [770],
    "RobotCurrent": [450],
    "I/OCurrent": [451],
    "PowerOn": [260],
    "ProtectiveStop": [261],
    "E-Stop": [262],                            # Robot Mode (e.g., running, idle)
    "TeachPressed": [263],
    "PowerPresses": [264],
    "StopRecommended": [265],
    "SafetyMode": [266],
    "RobotMode": [258]

}


# OPC UA Server configuration
OPC_SERVER_ENDPOINT = "opc.tcp://127.0.0.1:4840/freeopcua/server/"

def to_signed(val):
    if val>32768:
        return val-65535
    return val
async def main():
    # Initialize OPC UA server
    # cert_user_manager= CertificateUserManager()
    user_manager = UserManager()
    # await cert_user_manager.add_admin(
    #         "ThinkIQ.Opc.Ua.Client [2FF65ABC6B838E82CEB4C7DEC3A77149CE0EE150].der",
    #         name="ThinkIQ.Opc.Ua.Client"
    #     )

    # await cert_user_manager.add_admin(
    #         "ThinkIQ.Opc.Ua.Connector [2389399CBF50444980C5A85BD62C7807CBA16D58].der",
    #         name="ThinkIQ.Opc.Ua.Connector"
    #     )

    server_cert = Path("certs/certs/myserver-selfsigned.der")
    server_private_key = Path("certs/private/myserver.pem")
    host_name = socket.gethostname()
    server_app_uri = f"urn:{host_name}:freeopcua:python:server" # 
    # server_app_uri = f"myselfsignedserver@{host_name}"
    print(server_app_uri)



    server = Server(user_manager=user_manager)
    # server = Server()
    await server.init()
    await server.set_application_uri(server_app_uri)
    server.set_endpoint(OPC_SERVER_ENDPOINT)
    server.set_security_IDs(["Anonymous", "Basic256Sha256"])
    server.allow_remote_admin(True)
    namespace = await server.register_namespace("UR10e")
    server.default_timeout=100000

    # await setup_self_signed_certificate(
    #     server_private_key,
    #     server_cert,
    #     server_app_uri,
    #     host_name,
    #     [ExtendedKeyUsageOID.CLIENT_AUTH, ExtendedKeyUsageOID.SERVER_AUTH],
    #     {
    #     },
    # )

    # load server certificate and private key. This enables endpoints
    # with signing and encryption.
    await server.load_certificate(str(server_cert))
    await server.load_private_key(str(server_private_key))

    server.set_security_policy([
            ua.SecurityPolicyType.NoSecurity,
            ua.SecurityPolicyType.Basic256Sha256_SignAndEncrypt,
            ua.SecurityPolicyType.Basic256Sha256_Sign,
            ])

    # Create a new OPC UA node under Objects node
    objects = server.get_objects_node()

    # Add new objects for Modbus data under the namespace
    ur10e_object = await objects.add_object(namespace, "UR10eModbusData")

    # Create variables for each set of Modbus registers
    opc_variables = {}

    for reg_name, reg_list in MODBUS_REGISTERS.items():
        opc_variables[reg_name] = [
            await ur10e_object.add_variable(namespace, f"{reg_name}", ua.Int16(4))
            for i in reg_list
        ]
        # Set each variable as writable (just in case)
        for var in opc_variables[reg_name]:
            await var.set_writable()

    # Start OPC UA server
    await server.start()
    print(f"OPC UA server started at {OPC_SERVER_ENDPOINT}")
    # print(opc_variables)
    # Initialize Modbus client (asynchronous)
    while True:
        try:
            client = AsyncModbusTcpClient(UR10e_MODBUS_IP, port=MODBUS_PORT)
            await client.connect()
            print(f"Connected to Modbus server at {UR10e_MODBUS_IP}:{MODBUS_PORT}")
            # print("OPC Variables: ", opc_variables)
            while True:
                # Iterate through the Modbus register groups
                for reg_name, reg_list in MODBUS_REGISTERS.items():
                    for i, reg in enumerate(reg_list):
                        # Read each register from the UR10e robot
                        result = await client.read_holding_registers(reg, 1)
                        if result.isError():
                            print(f"Failed to read {reg_name} (Register {reg})")
                            print(f"Result: {result}")
                        else:
                            modbus_value = to_signed(result.registers[0])
                            # print("Modbus Value: ",(modbus_value))
                            # Update OPC UA node with Modbus data
                            await opc_variables[reg_name][i].write_value(ua.Int16(modbus_value))
                            # print(f"Updated {reg_name} (Register {reg}) with value: {modbus_value}")

                # print("Updated all modbus registers")
                await asyncio.sleep(0.5)  # Sleep for a while before fetching data again

        except asyncio.CancelledError:
            print("Shutting down...")
            break

        except pymodbus.exceptions.ConnectionException:
            print("Lost connection to modbus, trying to reconnect in 5 seconds")

    # Stop OPC UA server and disconnect Modbus client
    await server.stop()
    client.close()
    print("Server and Modbus client shut down.")


# Run the async main loop
if __name__ == "__main__":
    asyncio.run(main())

