function_calling_tools = [
    {
        "type": "function",
        "name": "update_customer_profile",
        "description": "Update customer profile information.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Customer name",
                },
                "email": {
                    "type": "string",
                    "description": "Customer email",
                },
                "phone": {
                    "type": "string",
                    "description": "Customer phone number",
                },
                "address": {
                    "type": "string",
                    "description": "Customer address",
                },
                "city": {
                    "type": "string",
                    "description": "Customer city",
                },
                "state": {
                    "type": "string",
                    "description": "Customer state",
                },
                "zip": {
                    "type": "string",
                    "description": "Customer zip code",
                },
            },
            "additionalProperties": False,
        },
    }
]
def make_function_call(function_call: dict):
    print(function_call)
    if function_call["name"] == "update_customer_profile":
        return update_customer_profile(function_call["arguments"])
    else:
        return "Function not found"

def update_customer_profile(arguments: dict):
    profile_details = ", ".join([f"{key}: {value}" for key, value in arguments.items() if value])
    return f"Customer profile updated with {profile_details}"