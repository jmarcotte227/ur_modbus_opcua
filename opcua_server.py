# Generated by ChatGPT
# Modified by the AMPS F24 Digital Manufacturing Team
#   -Brian Cooper
#   -Julia Gizzo
#   -Jack Marcotte
#   -Kaitlin McConnon
#   -Jaden Mirek

import asyncio
from pymodbus.client import AsyncModbusTcpClient
from asyncua import Server
from asyncua import ua
from asyncua.server.user_managers import CertificateUserManager
from asyncua.crypto.cert_gen import setup_self_signed_certificate
import logging
from pathlib import Path
from cryptography.x509.oid import ExtendedKeyUsageOID
import socket

logging.basicConfig(level=logging.WARNING)

# Configuration for the UR10e Modbus
UR10e_MODBUS_IP = '128.113.220.57'  # UR10e IP Address
MODBUS_PORT = 502                 # Standard Modbus TCP Port

# Define Modbus register ranges for UR10e robot data
MODBUS_REGISTERS = {
    "ActualJointPosition0": [270],
    "ActualJointPosition1": [271],
    "ActualJointPosition2": [272],
    "ActualJointPosition3": [273],
    "ActualJointPosition4": [274],
    "ActualJointPosition5": [275],
    "ActualJointVelocity0": [280],
    "ActualJointVelocity1": [281],
    "ActualJointVelocity2": [282],
    "ActualJointVelocity3": [283],
    "ActualJointVelocity4": [284],
    "ActualJointVelocity5": [285],
    "ToolPosition": list(range(400, 403)),         # Tool position (Cartesian, X, Y, Z)
    "ToolOrientation": list(range(403, 406)),      # Tool orientation (Quaternion)
    "JointCurrents": list(range(290, 296)),        # Actual current for each joint signed, ma
    "JointTemperatures": list(range(300, 306)),
    "JointRevolutionCount": list(range(320,326)),# Actual joint temperatures in °C
    "RobotCurrent": [450],
    "I/OCurrent": [451],
    "PowerOn": [260],
    "ProtectiveStop": [261],
    "E-Stop": [262],                            # Robot Mode (e.g., running, idle)
    "TeachPressed": [263],
    "PowerPresses": [264],
    "StopRecommended": [265]
}


# OPC UA Server configuration
OPC_SERVER_ENDPOINT = "opc.tcp://127.0.0.1:4840"

def to_signed(val):
    if val>32768:
        return val-65535
    return val
async def main():
    # Initialize OPC UA server
    # cert_user_manager= CertificateUserManager()
    # await cert_user_manager.add_admin(
    #         "ThinkIQ.Opc.Ua.Connector [23B9EA5C7A3DD59361B14486BC12A8DD248C38B2].der",
    #         name="test_user"
    #     )
    server_cert = Path("certs/certs/myserver-selfsigned.der")
    server_private_key = Path("certs/certs/myserver.pem")
    host_name = socket.gethostname()
    server_app_uri = f"urn:{host_name}:freeopcua:python:server" # 
    # server_app_uri = f"myselfsignedserver@{host_name}"
    print(server_app_uri)



    server = Server()
    # server = Server()
    await server.init()
    await server.set_application_uri(server_app_uri)
    server.set_endpoint(OPC_SERVER_ENDPOINT)
    server.set_security_IDs("Anonymous")
    namespace = await server.register_namespace("UR10eRobot")

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
            await ur10e_object.add_variable(namespace, f"{reg_name}_{i}", ua.Int16(4))
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
    client = AsyncModbusTcpClient(UR10e_MODBUS_IP, port=MODBUS_PORT)
    await client.connect()
    print(f"Connected to Modbus server at {UR10e_MODBUS_IP}:{MODBUS_PORT}")
    # print("OPC Variables: ", opc_variables)
    try:
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

            print("Updated all modbus registers")
            await asyncio.sleep(1)  # Sleep for a while before fetching data again

    except asyncio.CancelledError:
        print("Shutting down...")

    finally:
        # Stop OPC UA server and disconnect Modbus client
        await server.stop()
        client.close()
        print("Server and Modbus client shut down.")


# Run the async main loop
if __name__ == "__main__":
    asyncio.run(main())

