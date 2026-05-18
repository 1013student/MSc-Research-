import hashlib

proof = 0
index = 21
previous_hash = "abc1234"
transaction_data = [
	{ "index": 0, "sender": "mining", "recipient": "dea1af", "amount": 10.00, "signature": "" },
	{ "index": 1, "sender": "fea123", "recipient": "087efa", "amount": 5.00, "signature": "abcdef"}
]

blockStr = f"{index}{previous_hash}{str(transaction_data)}{proof}"

def calculate_hash(s):
    # Encode the string to bytes and calculate the hash
    # hexdigest() returns a hexadecimal string of the hash
    return hashlib.sha256(s.encode()).hexdigest()

while (1):
    hash_val = calculate_hash(blockStr)
    print(hash_val)
    if hash_val.startswith("0000"):
        break

    proof += 1
    blockStr = f"{index}{previous_hash}{str(transaction_data)}{proof}"

print(f"Proof of work found: {proof}")
print(calculate_hash(blockStr)) 