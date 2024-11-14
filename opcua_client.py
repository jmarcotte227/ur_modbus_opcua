from opcua import Client, ua

# Create a client
client = Client("opc.tcp://localhost:4840")

# Load the trust list (usually in the 'certificates' directory)
# client.load_certificate("client_certificate.der")
# client.load_private_key("client_private_key.pem")

# Add the server's certificate to the trust list (if not already present)
server_certificate = client.get_server_certificate()
client.security_policy_manager.trust_manager.add_trusted_certificate(server_certificate)

# Connect to the server
client.connect()
